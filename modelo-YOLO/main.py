import argparse
from pathlib import Path

from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "modelo-deteccion-placasv3-last.pt"

CONF_DETECCION = 0.45

_modelo = None


def cargar_modelo() -> YOLO:
    """
    Carga el modelo YOLOv8 (singleton, no se recarga en cada llamada).
    """
    global _modelo

    if _modelo is None:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"No se encontro el modelo en: {MODEL_PATH}"
            )
        _modelo = YOLO(str(MODEL_PATH))

    return _modelo


def hay_placa(imagen_path: str) -> bool:
    """
    Corre YOLOv8 sobre la imagen y devuelve True si detecto al menos
    una placa (segun CONF_DETECCION), False si no.
    """
    modelo = cargar_modelo()

    resultado = modelo.predict(
        imagen_path,
        conf=CONF_DETECCION,
        verbose=False,
    )[0]

    cajas = resultado.boxes

    return cajas is not None and len(cajas) > 0


def main():
    parser = argparse.ArgumentParser(
        description="Deteccion de placas vehiculares con YOLOv8"
    )

    parser.add_argument(
        "--imagen",
        required=True,
        help="Ruta de la imagen a analizar"
    )

    args = parser.parse_args()

    if hay_placa(args.imagen):
        print("Se detecto al menos una placa en la imagen.")
    else:
        print("No se detecto la placa")


if __name__ == "__main__":
    main()
