import argparse
import json
from pathlib import Path

from scraping_final import scrape_vehicle_image
from ocr.preprocess import preprocess_image
from ocr.read_image import extract_data_from_image


BASE_DIR = Path(__file__).resolve().parent


def run_pipeline(
    placa: str,
    gpu: bool = False,
    save_debug_rois: bool = True,
    replace_if_exists: bool = True
) -> dict:
    """
    Ejecuta el flujo completo del proyecto:

    1. Web scraping en SUNARP.
    2. Descarga de imagen.
    3. Preprocesamiento de imagen.
    4. OCR con ROIs fijos.
    5. Guardado en JSON individual.
    6. Actualización del JSON global.
    """

    placa = placa.upper().strip()

    print("=" * 70)
    print(f"INICIANDO PIPELINE PARA PLACA: {placa}")
    print("=" * 70)

    print("\n[1/3] Ejecutando scraping...")
    image_path = scrape_vehicle_image(placa)

    print("\n[2/3] Ejecutando preprocesamiento...")
    preprocess_result = preprocess_image(image_path)
    preprocessed_image_path = preprocess_result["output_path"]

    print("\n[3/3] Ejecutando OCR...")
    data = extract_data_from_image(
        image_name=preprocessed_image_path,
        save_debug_rois=save_debug_rois,
        gpu=gpu,
        replace_if_exists=replace_if_exists
    )

    print("\nProceso completado correctamente.")
    print("=" * 70)
    print(json.dumps(data, indent=4, ensure_ascii=False))

    return data


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline completo: scraping SUNARP + OCR + JSON"
    )

    parser.add_argument(
        "placa",
        help="Número de placa vehicular. Ejemplo: ADQ345"
    )

    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Usar GPU en EasyOCR si está disponible."
    )

    parser.add_argument(
        "--no-debug-rois",
        action="store_true",
        help="No guardar imágenes de depuración de los ROIs."
    )

    parser.add_argument(
        "--historico",
        action="store_true",
        help="Guardar cada consulta en el JSON global sin reemplazar registros anteriores."
    )

    args = parser.parse_args()

    run_pipeline(
        placa=args.placa,
        gpu=args.gpu,
        save_debug_rois=not args.no_debug_rois,
        replace_if_exists=not args.historico
    )


if __name__ == "__main__":
    main()
