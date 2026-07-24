import cv2
import json
import re
import easyocr
from pathlib import Path
from datetime import datetime


# ===============================================================
# Rutas base del proyecto
# ===============================================================

# read_ocr.py está en backend/ocr/read_ocr.py
# parents[0] = backend/ocr
# parents[1] = backend
BASE_DIR = Path(__file__).resolve().parents[1]

OCR_DIR = BASE_DIR / "ocr"
OCR_RESULTS_DIR = OCR_DIR / "results"

ROIS_PATH = OCR_DIR / "rois.json"

JSON_OUTPUT_DIR = OCR_DIR / "json"
JSON_BY_PLATE_DIR = JSON_OUTPUT_DIR / "placas"
MASTER_JSON_PATH = JSON_OUTPUT_DIR / "vehiculos.json"

DEBUG_ROI_DIR = OCR_RESULTS_DIR / "debug_rois"


# ===============================================================
# Limpieza de texto
# ===============================================================

def clean_text(text: str) -> str:
    """
    Limpieza general del texto extraído por OCR.
    """
    if not text:
        return ""

    text = text.replace("\n", " ")
    text = text.replace("|", "I")
    text = text.replace("°", "")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_plate(text: str) -> str:
    """
    Limpia placas vehiculares.
    """
    text = clean_text(text)
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text


def clean_year(text: str) -> str:
    """
    Limpia año de modelo.
    """
    text = clean_text(text)
    text = re.sub(r"[^0-9]", "", text)

    if len(text) >= 4:
        return text[:4]

    return text


def clean_date(text: str) -> str:
    """
    Limpia fecha de consulta.
    """
    text = clean_text(text)
    text = text.replace("O", "0")
    text = text.replace("o", "0")
    return text


def clean_owner_text(text: str) -> str:
    """
    Limpieza especial para propietarios.
    """
    text = clean_text(text)
    text = text.upper()

    text = text.replace("PROPIETARIO(S):", "")
    text = text.replace("PROPIETARIOS:", "")
    text = text.replace("PROPIETARIO:", "")
    text = text.replace("PROPIETARIO(S)", "")
    text = text.replace("PROPIETARIOS", "")
    text = text.replace("PROPIETARIO", "")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_field(field: str, text: str) -> str:
    """
    Aplica limpieza específica según el campo.
    """
    text = clean_text(text)

    if field in ["placa", "placa_vigente", "placa_anterior"]:
        return clean_plate(text)

    if field == "anio_modelo":
        return clean_year(text)

    if field == "fecha_consulta":
        return clean_date(text)

    if field == "propietarios":
        return clean_owner_text(text)

    return text.upper().strip()


# ===============================================================
# Utilidades
# ===============================================================

def read_rois_json(rois_path: Path) -> dict:
    """
    Lee el archivo rois.json.
    """
    if not rois_path.exists():
        raise FileNotFoundError(f"No existe el archivo de ROIs: {rois_path}")

    with open(rois_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_plate_name_from_image(image_path: Path) -> str:
    """
    Obtiene el nombre limpio de la placa desde la imagen preprocesada.

    Ejemplo:
    ADQ345_preprocessed.png  -> ADQ345
    ADQ345__preprocessed.png -> ADQ345
    """
    plate_name = image_path.stem
    plate_name = plate_name.replace("_preprocessed", "")
    plate_name = plate_name.rstrip("_")
    return plate_name


def read_text_from_roi(reader, roi, field: str) -> str:
    """
    Aplica EasyOCR sobre un ROI.
    """
    if field == "propietarios":
        result = reader.readtext(
            roi,
            detail=0,
            paragraph=True
        )
    else:
        result = reader.readtext(
            roi,
            detail=0,
            paragraph=False
        )

    if not result:
        return ""

    return " ".join(result)


# ===============================================================
# Guardado de JSON
# ===============================================================

def save_plate_json(data: dict, plate_name: str) -> Path:
    """
    Guarda un JSON individual por placa.

    Si la misma placa se procesa nuevamente, este archivo se sobrescribe.
    """
    JSON_BY_PLATE_DIR.mkdir(parents=True, exist_ok=True)

    plate_json_path = JSON_BY_PLATE_DIR / f"{plate_name}.json"

    with open(plate_json_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    return plate_json_path


def load_master_json() -> list:
    """
    Carga el JSON global.
    Si no existe, devuelve una lista vacía.
    """
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not MASTER_JSON_PATH.exists():
        return []

    with open(MASTER_JSON_PATH, "r", encoding="utf-8") as file:
        try:
            content = json.load(file)

            if isinstance(content, list):
                return content

            return []

        except json.JSONDecodeError:
            return []


def save_master_json(records: list) -> None:
    """
    Guarda la lista completa de registros en el JSON global.
    """
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(MASTER_JSON_PATH, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)


def upsert_master_json(data: dict, plate_name: str, replace_if_exists: bool = True) -> Path:
    """
    Guarda la información en el JSON global.

    replace_if_exists=True:
        Si la placa ya existe en vehiculos.json, actualiza el registro.

    replace_if_exists=False:
        Si la placa ya existe, agrega otro registro histórico.
    """

    records = load_master_json()

    record = {
        "placa_consultada": plate_name,
        "fecha_registro_ocr": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": data
    }

    if replace_if_exists:
        updated = False

        for index, existing_record in enumerate(records):
            if existing_record.get("placa_consultada") == plate_name:
                records[index] = record
                updated = True
                break

        if not updated:
            records.append(record)

    else:
        records.append(record)

    save_master_json(records)

    return MASTER_JSON_PATH


# ===============================================================
# Proceso OCR principal
# ===============================================================

def extract_data_from_image(
    image_name: str,
    save_debug_rois: bool = True,
    gpu: bool = False,
    replace_if_exists: bool = True
) -> dict:
    """
    Extrae datos de una imagen preprocesada usando los ROIs fijos.
    Guarda:
    1. JSON individual por placa.
    2. JSON global acumulativo.
    """

    image_path = OCR_RESULTS_DIR / image_name

    if not image_path.exists():
        raise FileNotFoundError(
            f"No existe la imagen preprocesada:\n{image_path}\n\n"
            f"Archivos encontrados en ocr/results:\n{list(OCR_RESULTS_DIR.glob('*'))}"
        )

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")

    rois = read_rois_json(ROIS_PATH)

    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_BY_PLATE_DIR.mkdir(parents=True, exist_ok=True)

    if save_debug_rois:
        DEBUG_ROI_DIR.mkdir(parents=True, exist_ok=True)

    reader = easyocr.Reader(["es", "en"], gpu=gpu)

    data = {}

    for field, box in rois.items():
        x = box["x"]
        y = box["y"]
        w = box["w"]
        h = box["h"]

        roi = image[y:y + h, x:x + w]

        if roi.size == 0:
            data[field] = ""
            continue

        if save_debug_rois:
            debug_roi_path = DEBUG_ROI_DIR / f"{field}.png"
            cv2.imwrite(str(debug_roi_path), roi)

        raw_text = read_text_from_roi(reader, roi, field)
        clean_value = normalize_field(field, raw_text)

        data[field] = clean_value

    plate_name = get_plate_name_from_image(image_path)

    plate_json_path = save_plate_json(data, plate_name)

    master_json_path = upsert_master_json(
        data=data,
        plate_name=plate_name,
        replace_if_exists=replace_if_exists
    )

    print("OCR completado correctamente.")
    print(f"Imagen procesada: {image_path}")
    print(f"JSON individual generado: {plate_json_path}")
    print(f"JSON global actualizado: {master_json_path}")

    return data


# ===============================================================
# Ejecución directa
# ===============================================================

if __name__ == "__main__":
    data = extract_data_from_image(
        image_name="X7I962_4_preprocessed.png",
        save_debug_rois=True,
        gpu=True,
        replace_if_exists=True
    )

    print("\nDatos extraídos:")
    print(json.dumps(data, indent=4, ensure_ascii=False))