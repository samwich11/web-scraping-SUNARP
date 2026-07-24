import cv2
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

OCR_DIR = BASE_DIR / "ocr"
OCR_RESULTS_DIR = OCR_DIR / "results"

ROIS_PATH = OCR_DIR / "rois.json"
DEBUG_PATH = OCR_RESULTS_DIR / "debug_fixed_rois.png"


# Dimensiones de referencia de tu imagen preprocesada
BASE_WIDTH = 675
BASE_HEIGHT = 710


def scale_box(box, current_width, current_height):
    """
    Escala las coordenadas si la imagen cambia ligeramente de tamaño.
    Si todas tus imágenes son 675x710, no cambia nada.
    """
    scale_x = current_width / BASE_WIDTH
    scale_y = current_height / BASE_HEIGHT

    return {
        "x": int(box["x"] * scale_x),
        "y": int(box["y"] * scale_y),
        "w": int(box["w"] * scale_x),
        "h": int(box["h"] * scale_y)
    }


def create_fixed_rois(image_name: str):
    image_path = OCR_RESULTS_DIR / image_name

    if not image_path.exists():
        raise FileNotFoundError(
            f"No existe la imagen preprocesada:\n{image_path}\n\n"
            f"Archivos encontrados:\n{list(OCR_RESULTS_DIR.glob('*'))}"
        )

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")

    height, width = image.shape[:2]

    # ROIs base para imagen preprocesada 675x710
    # Se selecciona principalmente la zona de los valores, no las etiquetas.
    # Coordenada común para todos los valores desde N° PLACA hasta AÑO DE MODELO
    # Empieza después de los ":" de "PLACA ANTERIOR:"
    VALUE_X = 245
    VALUE_W = 440
    VALUE_H = 30

    base_rois = {
        "placa": {
            "x": VALUE_X,
            "y": 63,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "serie": {
            "x": VALUE_X,
            "y": 94,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "vin": {
            "x": VALUE_X,
            "y": 125,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "motor": {
            "x": VALUE_X,
            "y": 158,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "color": {
            "x": VALUE_X,
            "y": 190,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "marca": {
            "x": VALUE_X,
            "y": 222,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "modelo": {
            "x": VALUE_X,
            "y": 254,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "placa_vigente": {
            "x": VALUE_X,
            "y": 286,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "placa_anterior": {
            "x": VALUE_X,
            "y": 318,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "estado": {
            "x": VALUE_X,
            "y": 350,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "anotaciones": {
            "x": VALUE_X,
            "y": 382,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "sede": {
            "x": VALUE_X,
            "y": 414,
            "w": VALUE_W,
            "h": VALUE_H
        },
        "anio_modelo": {
            "x": VALUE_X,
            "y": 446,
            "w": VALUE_W,
            "h": VALUE_H
        },

        # Propietarios se mantiene amplio porque puede tener varias líneas.
        "propietarios": {
            "x": 5,
            "y": 535,
            "w": 665,
            "h": 130
        },

        # Fecha de consulta
        "fecha_consulta": {
            "x": 5,
            "y": 675,
            "w": 300,
            "h": 30
        }
    }

    rois = {
        field: scale_box(box, width, height)
        for field, box in base_rois.items()
    }

    OCR_DIR.mkdir(parents=True, exist_ok=True)

    with open(ROIS_PATH, "w", encoding="utf-8") as file:
        json.dump(rois, file, indent=4, ensure_ascii=False)

    debug_image = image.copy()

    for field, box in rois.items():
        x = box["x"]
        y = box["y"]
        w = box["w"]
        h = box["h"]

        cv2.rectangle(
            debug_image,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cv2.putText(
            debug_image,
            field,
            (x, max(y - 5, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 255),
            1
        )

    cv2.imwrite(str(DEBUG_PATH), debug_image)

    print("ROIs generados correctamente.")
    print(f"Archivo JSON: {ROIS_PATH}")
    print(f"Imagen debug: {DEBUG_PATH}")
    print(f"Dimensiones de imagen usada: {width}x{height}")


if __name__ == "__main__":
    create_fixed_rois("ADQ345__preprocessed.png")