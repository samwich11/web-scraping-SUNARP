import argparse
import cv2
import numpy as np
import PIL.Image as Image
import easyocr

IDIOMAS_OCR = ["es", "en"]
ALLOWLIST_OCR = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"

_lector = None


def cargar_lector(gpu: bool = False) -> easyocr.Reader:
    """
    Carga EasyOCR (singleton, no se recarga en cada llamada).
    """
    global _lector

    if _lector is None:
        _lector = easyocr.Reader(IDIOMAS_OCR, gpu=gpu)

    return _lector

def cargar_imagen(imagen_path: str) -> np.ndarray:
    """
    Carga la imagen con PIL (soporta PNG con canal alfa, formatos raros, etc.)
    y la convierte a un array BGR de 3 canales, listo para EasyOCR/OpenCV.
    """
    pil_img = Image.open(imagen_path).convert("RGB")
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def extraer_textos(imagen_path: str, gpu: bool = False) -> list:
    """
    Corre EasyOCR UNA sola vez sobre la imagen original, sin ningun
    preprocesamiento (sin escala de grises, sin Otsu, sin adaptiveThreshold).

    Devuelve una lista de dicts con el texto TAL CUAL lo lee EasyOCR
    (sin limpiar ni poner en mayusculas) y su confianza:

        [{"texto": "ABC-123", "confianza": 0.91}, ...]
    """
    lector = cargar_lector(gpu=gpu)

    imagen = cargar_imagen(imagen_path)
    resultados = lector.readtext(imagen, allowlist=ALLOWLIST_OCR)

    textos = []
    for (_bbox, texto, confianza) in resultados:
        print(f"Texto: {texto}, Confianza: {confianza}")
        textos.append({
            "texto": texto,
            "confianza": round(float(confianza), 4),
        })

    return textos


def main():
    parser = argparse.ArgumentParser(
        description="Extraccion de texto de una imagen con EasyOCR"
    )

    parser.add_argument(
        "--imagen",
        required=True,
        help="Ruta de la imagen a analizar"
    )

    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Usar GPU en EasyOCR si esta disponible"
    )

    args = parser.parse_args()

    textos = extraer_textos(args.imagen, gpu=args.gpu)

    print(f"Textos detectados ({len(textos)}):")
    for t in textos:
        print(f"  - '{t['texto']}' (confianza: {t['confianza']})")


if __name__ == "__main__":
    main()
