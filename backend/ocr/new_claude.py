"""
ocr_sunarp.py
─────────────────────────────────────────────────────────────────────────────
Extrae datos vehiculares de imágenes de Consulta Vehicular SUNARP.

Flujo:
  1. Cargar imagen
  2. Limpiar marca de agua con threshold binario (método que ya funciona)
  3. Recortar cada campo por coordenadas calibradas
  4. OCR con EasyOCR por campo (más preciso que página completa)
  5. Parsear y limpiar el texto detectado
  6. Guardar resultado en JSON + imagen de debug con bboxes

Uso:
  python ocr_sunarp.py                         # usa RUTA_IMAGEN por defecto
  python ocr_sunarp.py ruta/imagen.png         # imagen específica
  python ocr_sunarp.py ruta/imagen.png -v      # modo verbose (confianza por bbox)

Requisitos:
  pip install easyocr opencv-python-headless
  (opencv-python-headless = misma API, sin GUI, menor tamaño)
"""

from __future__ import annotations

import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import easyocr

# ── Configuración ──────────────────────────────────────────────────────────────

RUTA_IMAGEN   = r"C:\Users\Daniel\Documents\Tech-Lab\web scraping\backend\results\ADQ345_3.png"
GPU           = False   # True solo si tenés CUDA instalado
UMBRAL_CONF   = 0.20    # Descartar detecciones con confianza < este valor
GUARDAR_DEBUG = True    # Exporta debug_<placa>.png con los bboxes dibujados
SALIDA_JSON   = True    # Exporta <placa>.json con los datos estructurados

# Dimensiones de referencia de la imagen SUNARP (540 × 680 px).
# Si tu imagen tiene otra resolución, las coordenadas se escalan automáticamente.
REF_W, REF_H = 540, 680

# ── Campos calibrados (x, y, ancho, alto) en coordenadas de referencia ────────
#
#  Cada tupla cubre la línea COMPLETA (etiqueta + valor).
#  EasyOCR detecta solo el texto dentro de ese recorte; el parseo posterior
#  extrae el valor eliminando la etiqueta.
#
CAMPOS: dict[str, tuple[int, int, int, int]] = {
    "placa":          (0, 158, 535, 24),
    "serie":          (0, 182, 535, 24),
    "vin":            (0, 206, 535, 24),
    "motor":          (0, 230, 535, 24),
    "color":          (0, 254, 535, 24),
    "marca":          (0, 278, 535, 24),
    "modelo":         (0, 302, 535, 24),
    "placa_vigente":  (0, 326, 535, 24),
    "placa_anterior": (0, 350, 535, 24),
    "estado":         (0, 374, 535, 24),
    "anotaciones":    (0, 398, 535, 24),
    "sede":           (0, 422, 535, 24),
    "anio_modelo":    (0, 446, 535, 24),
    "propietarios":   (0, 510, 535, 100),
    "fecha_consulta": (0, 640, 535, 24),
}

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)
log = logging.getLogger(__name__)


# ── Modelo de datos ────────────────────────────────────────────────────────────

@dataclass
class DatosVehiculo:
    placa:          str       = ""
    serie:          str       = ""
    vin:            str       = ""
    motor:          str       = ""
    color:          str       = ""
    marca:          str       = ""
    modelo:         str       = ""
    placa_vigente:  str       = ""
    placa_anterior: str       = ""
    estado:         str       = ""
    anotaciones:    str       = ""
    sede:           str       = ""
    anio_modelo:    str       = ""
    propietarios:   list[str] = field(default_factory=list)
    fecha_consulta: str       = ""
    # Metadatos de extracción
    imagen_origen:  str       = ""
    extraido_en:    str       = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def es_valido(self) -> bool:
        """True si los campos mínimos están presentes."""
        return bool(self.placa and self.serie and self.estado)


# ── Preprocesamiento ───────────────────────────────────────────────────────────

def preprocesar(ruta: Path) -> tuple[np.ndarray, np.ndarray, float, float]:
    """
    Lee y limpia la imagen.

    Retorna:
        img_color  — imagen limpia en BGR  (para dibujar debug encima)
        img_ocr    — imagen binarizada     (la que va a EasyOCR)
        escala_x   — factor de escala horizontal respecto a REF_W
        escala_y   — factor de escala vertical   respecto a REF_H
    """
    img = cv2.imread(str(ruta))
    if img is None:
        raise FileNotFoundError(f"No se pudo cargar: {ruta}")

    h, w = img.shape[:2]
    log.info("Imagen cargada: %d×%d px", w, h)

    escala_x = w / REF_W
    escala_y = h / REF_H

    # Binarización con threshold 150 (elimina la marca de agua gris)
    # Se opera sobre la imagen BGR; el resultado es binario (blanco/negro)
    _, img_ocr = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)

    # Versión en escala de grises para EasyOCR (más liviano que BGR)
    img_ocr_gray = cv2.cvtColor(img_ocr, cv2.COLOR_BGR2GRAY)

    return img_ocr, img_ocr_gray, escala_x, escala_y


# ── OCR por campo ──────────────────────────────────────────────────────────────

def ocr_campo(
    img_gray: np.ndarray,
    reader: easyocr.Reader,
    x: int, y: int, w: int, h: int,
    escala_x: float,
    escala_y: float,
    verbose: bool = False,
) -> tuple[str, list[dict]]:
    """
    Recorta el ROI escalado y corre EasyOCR sobre él.

    Retorna:
        texto_unido — texto del campo (todos los bloques concatenados)
        bboxes_abs  — lista de dicts con bbox en coordenadas absolutas de la imagen
                      (para dibujar en debug)
    """
    # Escalar coordenadas a la resolución real
    x1 = int(x * escala_x)
    y1 = int(y * escala_y)
    x2 = int((x + w) * escala_x)
    y2 = int((y + h) * escala_y)

    roi = img_gray[y1:y2, x1:x2]
    if roi.size == 0:
        return "", []

    resultados = reader.readtext(roi, detail=1, paragraph=False)

    fragmentos: list[str] = []
    bboxes_abs: list[dict] = []

    for bbox_local, texto, conf in resultados:
        # Asegurar que `conf` es numérico antes de usarlo
        try:
            conf_f = float(conf)
        except Exception:
            continue

        if conf_f < UMBRAL_CONF:
            continue
        if verbose:
            log.debug("  bbox=%s texto=%r conf=%.2f", bbox_local, texto, conf_f)

        fragmentos.append(texto.strip())

        # Convertir bbox local → coordenadas absolutas de la imagen original
        bbox_abs = [[int(int(pt[0]) + x1), int(int(pt[1]) + y1)] for pt in bbox_local]
        bboxes_abs.append({
            "texto": texto.strip(),
            "confianza": round(conf_f, 3),
            "bbox": bbox_abs,
        })

    return " ".join(fragmentos), bboxes_abs


# ── Parseo y limpieza de texto ─────────────────────────────────────────────────

# Prefijos de etiqueta que EasyOCR incluye en el recorte; hay que eliminarlos.
_PREFIJOS = re.compile(
    r"^(?:N[°º?'P]\s*)?(?:"
    r"PLACA\s+VIGENTE|PLACA\s+ANTERIOR|PLACA|SERIE|VIN|MOTOR|COLOR|MARCA|"
    r"MODELO|ESTADO|ANOTACIONES|SEDE|A[ÑN]O\s+DE\s+MODELO"
    r")\s*[:\-]?\s*",
    re.IGNORECASE,
)

# Corrección de confusiones OCR en campos con formato conocido (placa, VIN, etc.)
_CORR_ALFANUM = str.maketrans("OoIlSsBbGg", "0011558860")

_CAMPOS_ALFANUM = {"placa", "serie", "vin", "motor", "placa_vigente", "placa_anterior"}

_RE_FECHA = re.compile(r"\d{2}[/.-]\d{2}[/.-]\d{4}\s+\d{2}[:.]\d{2}[:.]\d{2}")


def limpiar_valor(campo: str, texto: str) -> str | list[str]:
    """
    Elimina el prefijo de etiqueta del texto y aplica correcciones según el campo.
    Para 'propietarios' devuelve lista; para el resto devuelve str.
    """
    texto = re.sub(r"\s+", " ", texto).strip()

    if campo == "propietarios":
        # Dividir por coma+mayúscula (cada nombre ocupa una línea)
        # EasyOCR puede unirlos; separamos por / o nueva detección
        nombres = [n.strip() for n in re.split(r"\s{2,}|/", texto) if n.strip()]
        # Filtrar línea de encabezado "PROPIETARIO(S):"
        nombres = [n for n in nombres if not re.match(r"PROPIETARIO", n, re.I)]
        return nombres

    if campo == "fecha_consulta":
        m = _RE_FECHA.search(texto)
        return m.group(0).replace(".", ":") if m else texto

    # Eliminar prefijo de etiqueta
    texto = _PREFIJOS.sub("", texto).strip()

    # Corrección alfanumérica en campos con formato conocido
    if campo in _CAMPOS_ALFANUM and texto:
        texto = texto.upper().translate(_CORR_ALFANUM)

    return texto


# ── Debug visual ───────────────────────────────────────────────────────────────

def dibujar_bboxes(
    img_color: np.ndarray,
    todos_bboxes: dict[str, list[dict]],
    ruta_salida: str,
) -> None:
    """
    Dibuja los bboxes detectados sobre la imagen, coloreados por confianza:
      Verde  (≥ 0.70): alta confianza
      Naranja (≥ 0.40): confianza media
      Rojo   (< 0.40): baja confianza
    """
    debug = img_color.copy()

    for campo, bboxes in todos_bboxes.items():
        for item in bboxes:
            conf  = item["confianza"]
            pts   = np.array(item["bbox"], dtype=np.int32)
            color = (0, 200, 0) if conf >= 0.70 else (0, 165, 255) if conf >= 0.40 else (0, 0, 220)

            cv2.polylines(debug, [pts], isClosed=True, color=color, thickness=1)
            # Etiqueta pequeña con campo y confianza
            label = f"{campo[:6]} {conf:.2f}"
            cv2.putText(
                debug, label,
                (pts[0][0], max(pts[0][1] - 3, 10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.28, color, 1,
            )

    cv2.imwrite(ruta_salida, debug)
    log.info("Debug guardado: %s", ruta_salida)


# ── Serialización JSON ─────────────────────────────────────────────────────────

def guardar_json(datos: DatosVehiculo, ruta_salida: str) -> None:
    d = asdict(datos)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    log.info("JSON guardado: %s", ruta_salida)


# ── Formato de tabla en consola ────────────────────────────────────────────────

_ETIQUETAS_DISPLAY = {
    "placa":          "N° PLACA",
    "serie":          "N° SERIE",
    "vin":            "N° VIN",
    "motor":          "N° MOTOR",
    "color":          "COLOR",
    "marca":          "MARCA",
    "modelo":         "MODELO",
    "placa_vigente":  "PLACA VIGENTE",
    "placa_anterior": "PLACA ANTERIOR",
    "estado":         "ESTADO",
    "anotaciones":    "ANOTACIONES",
    "sede":           "SEDE",
    "anio_modelo":    "AÑO DE MODELO",
    "propietarios":   "PROPIETARIO(S)",
    "fecha_consulta": "FECHA CONSULTA",
}

def imprimir_tabla(datos: DatosVehiculo) -> None:
    W = 56
    print(f"\n┌{'─' * W}┐")
    print(f"│{'DATOS DEL VEHÍCULO — SUNARP':^{W}}│")
    print(f"├{'─' * W}┤")

    d = asdict(datos)
    for campo, etiqueta in _ETIQUETAS_DISPLAY.items():
        valor = d[campo]

        if campo == "propietarios":
            nombres = valor if isinstance(valor, list) else [valor]
            print(f"│  {'PROPIETARIO(S)':<22}{'':>{W - 24}}  │")
            for nombre in nombres:
                n = nombre[:W - 4]
                print(f"│    {n:<{W - 4}}│")
        else:
            v = str(valor) if valor else "—"
            linea = f"  {etiqueta:<22}  {v}"
            if len(linea) > W:
                linea = linea[:W - 1] + "…"
            print(f"│{linea:<{W}}│")

    print(f"└{'─' * W}┘")
    if not datos.es_valido():
        print("\n⚠  Faltan campos obligatorios. Revisá la imagen o bajá UMBRAL_CONF.")


# ── Main ───────────────────────────────────────────────────────────────────────

def procesar(ruta_str: str, verbose: bool = False) -> DatosVehiculo:
    ruta = Path(ruta_str)
    if not ruta.exists():
        log.error("Imagen no encontrada: %s", ruta)
        sys.exit(1)

    # 1. Preprocesar
    img_color, img_gray, sx, sy = preprocesar(ruta)

    # 2. Inicializar EasyOCR una sola vez
    log.info("Cargando EasyOCR (gpu=%s)…", GPU)
    reader = easyocr.Reader(["es", "en"], gpu=GPU, verbose=False)

    # 3. OCR campo por campo
    datos = DatosVehiculo(imagen_origen=ruta.name)
    todos_bboxes: dict[str, list[dict]] = {}

    log.info("Extrayendo campos…")
    for campo, (x, y, w, h) in CAMPOS.items():
        texto_raw, bboxes = ocr_campo(
            img_gray, reader, x, y, w, h, sx, sy, verbose=verbose
        )
        todos_bboxes[campo] = bboxes

        # Limpiar y asignar al dataclass
        valor = limpiar_valor(campo, texto_raw)
        setattr(datos, campo, valor)

        if verbose:
            log.info("  %-18s → %r", campo, valor)

    # 4. Debug visual
    if GUARDAR_DEBUG:
        nombre_debug = f"debug_{datos.placa or 'sin_placa'}.png"
        dibujar_bboxes(img_color, todos_bboxes, nombre_debug)

    # 5. JSON
    if SALIDA_JSON:
        nombre_json = f"{datos.placa or 'resultado'}.json"
        guardar_json(datos, nombre_json)

    # 6. Consola
    imprimir_tabla(datos)

    return datos


if __name__ == "__main__":
    args   = sys.argv[1:]
    ruta   = args[0] if args else RUTA_IMAGEN
    verbose = "-v" in args or "--verbose" in args
    procesar(ruta, verbose=verbose)