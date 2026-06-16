"""
OCR mejorado para imágenes de Consulta Vehicular SUNARP.

Diagnóstico del problema original:
- El script anterior intentaba eliminar la marca de agua con inpainting HSV,
  pero el rango era tan amplio que destruía píxeles del propio texto.
- La imagen con recuadros de debug (debug_campos.png) se usaba en lugar
  de la imagen limpia, añadiendo ruido extra.

Solución:
- Limpiar SOLO los píxeles de muy alta saturación (marca azul/violeta) → blanco.
- Usar la imagen completa (no por campo) con Tesseract PSM 4 para detección
  automática del layout y extracción limpia de todas las líneas.
- Parsear el texto resultante con expresiones regulares.
- Los recuadros de debug se dibujan sobre una COPIA separada y nunca
  interfieren con la imagen que se pasa al OCR.

Requisitos:
    pip install pytesseract opencv-python pillow
    + tesseract instalado con paquete de idioma español:
        Windows: https://github.com/UB-Mannheim/tesseract/wiki
        Linux:   sudo apt install tesseract-ocr tesseract-ocr-spa
"""

import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from pathlib import Path

# ── Configuración ─────────────────────────────────────────────────────────────

RUTA_IMAGEN   = r"C:\Users\Daniel\Documents\Tech-Lab\web scraping\backend\results\ADQ345_3.png"
GUARDAR_DEBUG = True          # Genera debug_campos.png con los recuadros de diagnóstico
ESCALA        = 3             # Factor de ampliación antes del OCR (3 recomendado)

# Ruta a tesseract.exe (solo necesario en Windows si no está en PATH)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ── 1. Limpieza de marca de agua ───────────────────────────────────────────────

# def limpiar_marca_agua(imagen: np.ndarray) -> np.ndarray:
#     """
#     Neutraliza la marca de agua SUNARP eliminando solo los píxeles con alta
#     saturación de color (azul/violeta: HSV S > 100).  El texto real es negro
#     puro (S ≈ 0), por lo que no se ve afectado.

#     NO usa inpainting (que destruía el texto oscuro vecino).
#     Reemplaza directamente por blanco los píxeles de la marca coloreada.
#     """
#     hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
#     s_channel = hsv[:, :, 1]
#     v_channel = hsv[:, :, 2]

#     # Píxeles con color pronunciado y brillo mínimo → marca de agua
#     mascara = (s_channel > 100) & (v_channel > 20)

#     resultado = imagen.copy()
#     resultado[mascara] = [255, 255, 255]
#     return resultado


# ── 2. Preprocesamiento para OCR ───────────────────────────────────────────────

# def preparar_para_ocr(imagen: np.ndarray) -> np.ndarray:
#     """
#     Convierte a escala de grises, amplía y aplica umbral adaptativo.
#     Devuelve imagen lista para Tesseract.
#     """
#     gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
#     gris = cv2.resize(gris, None, fx=ESCALA, fy=ESCALA,
#                       interpolation=cv2.INTER_CUBIC)
#     return gris


# ── 3. OCR de página completa ──────────────────────────────────────────────────

# def ocr_pagina_completa(imagen_preprocesada: np.ndarray) -> str:
#     """
#     Corre Tesseract en modo PSM 4 (columna única de tamaño variable),
#     que detecta automáticamente el layout de etiqueta: valor.
#     """
#     pil = Image.fromarray(imagen_preprocesada)
#     config = "--oem 3 --psm 4 -l spa+eng"
#     return pytesseract.image_to_string(pil, config=config)


# ── 4. Parseo del texto extraído ───────────────────────────────────────────────

# Mapeo: fragmentos detectables en el texto → clave de salida
PATRONES_CAMPO = [
    ("placa",          r"PLACA[:\s]+([A-Z0-9]{5,8})\b"),
    ("serie",          r"SERIE[:\s]+([A-Z0-9]{10,20})"),
    ("vin",            r"VIN[:\s]+([A-Z0-9]{10,20})"),
    ("motor",          r"MOTOR[:\s]+([A-Z0-9]{6,15})"),
    ("color",          r"COLOR[:\s]+([A-Z\s]{3,30})"),
    ("marca",          r"MARCA[:\s]+([A-Z\s]{2,20})"),
    ("modelo",         r"MODELO[:\s]+([A-Z0-9\s]{2,20})"),
    ("placa_vigente",  r"PLACA\s+VIGENTE[:\s]+([A-Z0-9]{5,8})"),
    ("placa_anterior", r"PLACA\s+ANTERIOR[:\s]+([A-Z0-9IO]{5,8})"),
    ("estado",         r"ESTADO[:\s]+([A-Z\s]{3,30})"),
    ("anotaciones",    r"ANOTACIONES[:\s]+([A-Z\s]{3,30})"),
    ("sede",           r"SEDE[:\s]+([A-Z\s]{2,20})"),
    ("anio_modelo",    r"(?:ANO|AÑO)\s+DE\s+MODELO[:\s]+([0-9]{0,4})"),
]

def parsear_texto(texto_ocr: str) -> dict:
    """
    Extrae los campos vehiculares del texto plano devuelto por Tesseract
    usando expresiones regulares tolerantes a errores de OCR.
    """
    # Normalizar: colapsar espacios y convertir a mayúsculas
    texto = re.sub(r"\s+", " ", texto_ocr).upper().strip()

    datos = {}

    for clave, patron in PATRONES_CAMPO:
        m = re.search(patron, texto)
        datos[clave] = m.group(1).strip() if m else ""

    # Propietarios: todo lo que viene después de PROPIETARIO(S):
    m_prop = re.search(
        r"PROPIETARIO\(?S?\)?[:\s]+([\s\S]+?)(?:\d{2}/\d{2}/\d{4}|$)",
        texto
    )
    if m_prop:
        lineas = [l.strip() for l in m_prop.group(1).split("\n") if l.strip()]
        datos["propietarios"] = " / ".join(lineas)
    else:
        datos["propietarios"] = ""

    return datos


# ── 5. Debug visual (sin afectar el OCR) ──────────────────────────────────────

CAMPOS_DEBUG = {
    "placa":          (185, 158, 200, 26),
    "serie":          (185, 183, 320, 26),
    "vin":            (185, 208, 320, 26),
    "motor":          (185, 233, 215, 26),
    "color":          (185, 258, 230, 26),
    "marca":          (185, 283, 200, 26),
    "modelo":         (185, 308, 200, 26),
    "vigente":        (185, 333, 200, 26),
    "anterior":       (185, 358, 200, 26),
    "estado":         (185, 383, 240, 26),
    "anotaciones":    (185, 408, 240, 26),
    "sede":           (185, 433, 200, 26),
    "anio_modelo":    (185, 458, 200, 26),
    "propietarios":   (5,   507, 530, 115),
}

def guardar_debug(imagen_limpia: np.ndarray, ruta: str = "debug_campos.png"):
    """
    Dibuja los recuadros de diagnóstico sobre una COPIA de la imagen limpia.
    Nunca modifica la imagen usada para OCR.
    """
    debug = imagen_limpia.copy()
    for campo, (x, y, w, h) in CAMPOS_DEBUG.items():
        cv2.rectangle(debug, (x, y), (x + w, y + h), (0, 200, 0), 1)
        cv2.putText(debug, campo, (x, max(y - 3, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 200), 1)
    cv2.imwrite(ruta, debug)
    print(f"[DEBUG] Imagen de diagnóstico guardada: {ruta}")


# ── 6. Función principal ───────────────────────────────────────────────────────

def extraer_datos_vehiculo(ruta: str) -> tuple[dict, str]:
    print(f"[INFO] Leyendo imagen: {ruta}")
    imagen = cv2.imread(ruta)
    if imagen is None:
        raise FileNotFoundError(f"No se pudo leer la imagen: {ruta}")

    h, w = imagen.shape[:2]
    print(f"[INFO] Resolución: {w}×{h} px")

    # Paso 1 — Limpiar marca de agua (solo pixels muy saturados → blanco)
    print("[INFO] Limpiando marca de agua (alta saturación)…")
    # imagen_limpia = limpiar_marca_agua(imagen)

    # Paso 2 — Guardar debug sobre la imagen limpia (NO sobre la que irá al OCR)
    if GUARDAR_DEBUG:
        # guardar_debug(imagen_limpia)
        pass

    # Paso 3 — Preparar para OCR (ampliar + escala de grises)
    print("[INFO] Preparando imagen para OCR…")
    # img_ocr = preparar_para_ocr(imagen_limpia)

    # Paso 4 — OCR de página completa
    print("[INFO] Ejecutando OCR (Tesseract PSM 4)…")
    # texto_raw = ocr_pagina_completa(img_ocr)

    if not texto_raw.strip():
        print("[WARN] Tesseract no devolvió texto. Verificá que tesseract-ocr-spa esté instalado.")

    # Paso 5 — Parsear resultado
    datos = parsear_texto(texto_raw)
    return datos, texto_raw


# ── 7. Ejecución ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    datos, texto_raw = extraer_datos_vehiculo(RUTA_IMAGEN)

    ETIQUETAS = {
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
    }

    print("\n" + "═" * 50)
    print("        DATOS DEL VEHÍCULO — SUNARP")
    print("═" * 50)
    for campo, valor in datos.items():
        etiqueta = ETIQUETAS.get(campo, campo.upper())
        print(f"  {etiqueta:<20}: {valor}")
    print("═" * 50)

    # Mostrar texto raw para depuración (comentar si no se necesita)
    print("\n[RAW OCR]")
    print(texto_raw)