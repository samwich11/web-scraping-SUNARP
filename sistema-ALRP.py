import argparse
import importlib.util
import logging
import re
import sys
import warnings
from pathlib import Path

# Warning para guardar la salida de consola limpia
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", category=UserWarning, module="torch.ao")

BASE_DIR = Path(__file__).resolve().parent

# 3 caracteres alfanumericos + guion + 3 numeros, ej: ABC-123
PATRON_PLACA = re.compile(r"^[A-Z0-9]{3}-?\d{3}$")

logger = logging.getLogger("sistema_alpr")


def configurar_logging(debug: bool = False) -> None:
    # Configura el logger con un formato limpio para que la salida en consola sea legible.
    nivel = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=nivel, format="%(message)s")


def cargar_modulo(nombre: str, ruta: Path):
    # Carga los modulo del sistema ALRP a partir de su ruta absoluta.
    
    sys.path.insert(0, str(ruta.parent))

    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)

    return modulo


def encabezado(texto: str) -> None:
    # Imprime un encabezado de paso con separador uniforme.
    logger.info("── %s ──", texto)


def main():
    parser = argparse.ArgumentParser(
        description="Sistema ALPR: YOLOv8 (deteccion) + EasyOCR (lectura) "
                     "+ scraping SUNARP"
    )

    parser.add_argument(
        "--imagen",
        required=True,
        help="Ruta de la imagen a analizar"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Muestra detalle tecnico adicional (rutas, trazas, etc.)"
    )

    parser.add_argument(
        "--output",
        default="resultados",
        help="Carpeta base donde se guardara la imagen con bounding boxes (por defecto: 'resultados')"
    )

    args = parser.parse_args()
    configurar_logging(debug=args.debug)

    imagen_path = args.imagen
    logger.debug("Imagen recibida: %s", imagen_path)

    yolo_main = cargar_modulo("yolo_main", BASE_DIR / "modelo-YOLO" / "main.py")
    ocr_main = cargar_modulo("ocr_main", BASE_DIR / "modelo-OCR" / "main.py")
    backend_main = cargar_modulo("backend_main", BASE_DIR / "backend" / "main.py")

    # -----------------------------------------------------------------
    # 1. YOLOv8: verificar cuantas placas hay en la imagen
    # -----------------------------------------------------------------
    encabezado("Paso 1/3: Deteccion de placa (YOLOv8)")

    total_placas, resultado_yolo = yolo_main.detectar_placas(imagen_path)

    if total_placas == 0:
        logger.info("No se detecto la placa")
        return

    logger.info("Se detectaron %d placa(s):", total_placas)

    cajas = resultado_yolo.boxes
    if cajas is not None:
        for i, caja in enumerate(cajas, start=1):
            confianza_deteccion = float(caja.conf[0])
            logger.info("  - Placa %d (confianza deteccion: %.4f)", i, confianza_deteccion)

    ruta_guardada = yolo_main.dibujar_y_guardar(imagen_path, resultado_yolo, args.output)
    logger.info("Imagen con bounding boxes guardada en: %s", ruta_guardada)

    logger.info("Continuando con OCR y scraping SUNARP...")

    # -----------------------------------------------------------------
    # 2. EasyOCR: extraer todos los textos de la imagen ORIGINAL
    # -----------------------------------------------------------------
    encabezado("Paso 2/3: Lectura de texto (EasyOCR)")

    textos_detectados = ocr_main.extraer_textos(imagen_path)

    if not textos_detectados:
        logger.info("No se detecto texto en la imagen")
        return

    logger.info("Textos detectados (%d):", len(textos_detectados))

    placas_validas = []
    for t in textos_detectados:
        es_valido = bool(PATRON_PLACA.match(t["texto"]))
        estado = "valido" if es_valido else "no valido"
        logger.info("  - '%s' (confianza: %s) -> %s", t["texto"], t["confianza"], estado)

        if es_valido:
            placas_validas.append(t)

    if not placas_validas:
        logger.info("No hay placas legibles")
        return

    # -----------------------------------------------------------------
    # 3. Scraping SUNARP por cada placa valida
    # -----------------------------------------------------------------
    encabezado("Paso 3/3: Consulta SUNARP")

    for p in placas_validas:
        placa = p["texto"]

        encabezado(f"Placa {placa}: iniciando consulta SUNARP")

        try:
            backend_main.run_pipeline(placa)
        except Exception as e:
            logger.error("Error al procesar la placa %s: %s", placa, e)


if __name__ == "__main__":
    main()
