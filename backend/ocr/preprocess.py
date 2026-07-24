# import cv2
# from backend.scraping import PLACA

# #===============================================================
# # Eliminar marca de agua y recortar encabezado
# #=============================================================== 
# ruta = r'C:\Users\Daniel\Documents\Tech-Lab\web scraping\backend\results\ADQ345_.png'

# # Escala de grises
# imagen = cv2.imread(ruta, cv2.COLOR_BGR2GRAY)

# if imagen is None:
#     raise FileNotFoundError(f'No se pudo cargar la imagen: {ruta}')

# # Binarización
# _, imagen_limpia = cv2.threshold(imagen, 150, 255, cv2.THRESH_BINARY)

# # Guardar imagen sin marca de agua
# cv2.imwrite(f'imagen_sin_marca.png', imagen_limpia)

# # print("Imagen procesada y guardada como 'imagen_sin_marca.png'.")

# # Obtener dimensiones de la imagen
# alto, ancho = imagen_limpia.shape[:2]

# # Recortar encabezado
# x_inicio = 0
# y_inicio = 140      # Elimina el encabezado
# x_fin = ancho
# y_fin = alto

# imagen_recortada = imagen_limpia[y_inicio:y_fin, x_inicio:x_fin]

# # Guardar imagen recortada
# cv2.imwrite(f'imagen_recortada_{PLACA}.png', imagen_recortada)

# if __name__ == "__main__":
#     print("Preprocesamiento completado. Imagen recortada guardada como 'imagen_recortada.png'.")
#     # Imprimir información de la imagen recortada
#     print(f"Imagen recortada y guardada como 'imagen_recortada_{PLACA}.png'.")
#     print(f"Dimensiones originales: {ancho}x{alto}")
#     print(f"Dimensiones recortadas: {imagen_recortada.shape}")
#     print(f"Dimensiones recortadas: {imagen_recortada.shape[1]}x{imagen_recortada.shape[0]}")


import cv2
from pathlib import Path

# Ruta base del backend
# preprocess.py está en backend/ocr/preprocess.py
BASE_DIR = Path(__file__).resolve().parents[1]

RESULTS_DIR = BASE_DIR / "results"
OCR_RESULTS_DIR = BASE_DIR / "ocr" / "results"

# La imagen con la que se definieron los ROI mide 675x850 antes de quitar
# el encabezado y 675x710 después del recorte de 140 px.
REFERENCE_WIDTH = 675
REFERENCE_HEIGHT = 850


def preprocess_image(
    image_path: str | Path,
    output_dir: str | Path = OCR_RESULTS_DIR,
    crop_header: int = 140,
    reference_width: int = REFERENCE_WIDTH,
    reference_height: int = REFERENCE_HEIGHT,
):
    """
    Preprocesa la imagen obtenida del scraping:
    1. Carga la imagen en escala de grises.
    2. Normaliza su tamaño al usado para definir los ROI.
    3. Aplica binarización.
    4. Recorta el encabezado.
    5. Guarda la imagen procesada.
    """

    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not image_path.exists():
        raise FileNotFoundError(f"No existe la imagen: {image_path}")

    image_gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

    if image_gray is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")

    source_height, source_width = image_gray.shape[:2]

    if reference_width <= 0 or reference_height <= 0:
        raise ValueError("Las dimensiones de referencia deben ser mayores que cero.")

    # SUNARP entrega la misma ficha en distintas resoluciones (por ejemplo,
    # 540x680 y 675x850). Normalizar antes del recorte conserva la posición
    # de todos los campos respecto de los ROI originales.
    if (source_width, source_height) != (reference_width, reference_height):
        image_gray = cv2.resize(
            image_gray,
            (reference_width, reference_height),
            interpolation=cv2.INTER_CUBIC,
        )

    _, image_binary = cv2.threshold(
        image_gray,
        150,
        255,
        cv2.THRESH_BINARY
    )

    height, width = image_binary.shape[:2]

    if not 0 <= crop_header < height:
        raise ValueError(
            f"crop_header debe estar entre 0 y {height - 1}; recibido: {crop_header}"
        )

    image_cropped = image_binary[crop_header:height, 0:width]

    plate = image_path.stem
    output_path = output_dir / f"{plate}_preprocessed.png"

    cv2.imwrite(str(output_path), image_cropped)

    return {
        "plate": plate,
        "original_width": source_width,
        "original_height": source_height,
        "normalized_width": width,
        "normalized_height": height,
        "processed_width": image_cropped.shape[1],
        "processed_height": image_cropped.shape[0],
        "output_path": str(output_path)
    }


if __name__ == "__main__":
    image_name = "X7I962_4.png"

    result = preprocess_image(
        image_path=RESULTS_DIR / image_name,
        output_dir=OCR_RESULTS_DIR,
        crop_header=140
    )

    print("Preprocesamiento completado")
    print(f"Placa: {result['plate']}")
    print(f"Imagen procesada: {result['output_path']}")
    print(f"Dimensiones originales: {result['original_width']}x{result['original_height']}")
    print(f"Dimensiones procesadas: {result['processed_width']}x{result['processed_height']}")
