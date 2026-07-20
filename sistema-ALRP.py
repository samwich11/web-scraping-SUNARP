import argparse
import importlib.util
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# 3 caracteres alfanumericos + guion + 3 numeros, ej: ABC-123
PATRON_PLACA = re.compile(r"^[A-Z0-9]{3}-?\d{3}$")


def cargar_modulo(nombre: str, ruta: Path):
    """
    Carga un archivo .py como modulo Python a partir de su ruta absoluta.
    Se usa importlib (en vez de un import normal) porque las carpetas
    'modelo-YOLO' y 'modelo-OCR' tienen guiones y no son nombres de
    paquete validos para un 'import' estandar.

    Tambien agrega la carpeta del modulo a sys.path, para que los imports
    relativos que hace ese modulo (ej. backend/main.py importando
    'scraping_gpt' o 'ocr.preprocess') sigan funcionando igual que si se
    ejecutara ese archivo directamente desde su propia carpeta.
    """
    sys.path.insert(0, str(ruta.parent))

    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)

    return modulo


yolo_main = cargar_modulo("yolo_main", BASE_DIR / "modelo-YOLO" / "main.py")
ocr_main = cargar_modulo("ocr_main", BASE_DIR / "modelo-OCR" / "main.py")
backend_main = cargar_modulo("backend_main", BASE_DIR / "backend" / "main.py")


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

    args = parser.parse_args()
    imagen_path = args.imagen

    # -----------------------------------------------------------------
    # 1. YOLOv8: verificar si hay una placa en la imagen
    # -----------------------------------------------------------------
    print("[1/3] Verificando si hay una placa en la imagen (YOLOv8)...")

    if not yolo_main.hay_placa(imagen_path):
        print("No se detecto la placa")
        return

    "Se detecto una(s) placa(s) en la imagen, continuando con OCR y scraping SUNARP..."

    # -----------------------------------------------------------------
    # 2. EasyOCR: extraer todos los textos de la imagen ORIGINAL
    # -----------------------------------------------------------------
    print("[2/3] Extrayendo texto de la imagen (EasyOCR)...")

    textos_detectados = ocr_main.extraer_textos(imagen_path)

    # Validar cada texto TAL CUAL lo devuelve EasyOCR (sin limpiar)
    # contra el patron de placa: 3 alfanumericos + guion + 3 numeros
    placas_validas = [
        item for item in textos_detectados
        if PATRON_PLACA.match(item["texto"])
    ]

    if not placas_validas:
        print("No hay placas legibles")
        return

    print(f"\nPlacas validas encontradas ({len(placas_validas)}):")
    for p in placas_validas:
        print(f"  - {p['texto']} (confianza OCR: {p['confianza']})")

    # -----------------------------------------------------------------
    # 3. Scraping SUNARP por cada placa valida
    # -----------------------------------------------------------------
    print("\n[3/3] Consultando SUNARP para cada placa valida...")

    for p in placas_validas:
        placa = p["texto"]

        print("\n" + "=" * 70)
        print(f"PLACA: {placa}")
        print("=" * 70)

        try:
            backend_main.run_pipeline(placa)
        except Exception as e:
            print(f"Error al procesar la placa {placa}: {e}")


if __name__ == "__main__":
    main()
