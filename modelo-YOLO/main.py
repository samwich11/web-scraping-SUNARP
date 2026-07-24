import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "modelo-deteccion-placasv3-last.pt"

CONF_DETECCION = 0.45

_modelo = None


def cargar_modelo() -> YOLO:
    
    # Carga el modelo YOLOv8 (singleton, no se recarga en cada llamada).
    
    global _modelo

    if _modelo is None:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"No se encontro el modelo en: {MODEL_PATH}"
            )
        _modelo = YOLO(str(MODEL_PATH))

    return _modelo


def detectar_placas(imagen_path: str):
    
    # Corre YOLOv8 sobre la imagen y devuelve una tupla:
    # 
    # total_placas: cantidad de placas detectadas.
    # resultado_yolo: objeto Results de ultralytics, usado luego para dibujar los bounding boxes.
    
    modelo = cargar_modelo()

    resultado = modelo.predict(
        imagen_path,
        conf=CONF_DETECCION,
        verbose=False,
    )

    resultado = resultado[0]  # Solo nos interesa el primer resultado (la imagen original)

    cajas = resultado.boxes
    total_placas = 0 if cajas is None else len(cajas)

    return total_placas, resultado


def dibujar_y_guardar(imagen_path: str, resultado, output_dir: str = "resultados") -> str:
    
    # Dibuja los bounding boxes de las placas detectadas sobre la imagen original
    
    imagen_path = Path(imagen_path)

    imagen = cv2.imread(str(imagen_path))
    if imagen is None:
        raise FileNotFoundError(f"No se pudo leer la imagen: {imagen_path}")

    cajas = resultado.boxes

    for caja in cajas:
        x1, y1, x2, y2 = map(int, caja.xyxy[0])
        confianza = float(caja.conf[0])

        cv2.rectangle(imagen, (x1, y1), (x2, y2), (0, 255, 0), 10)

        etiqueta = f"{confianza:.2f}"
        (texto_w, texto_h), _ = cv2.getTextSize(
            etiqueta, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )
        cv2.rectangle(
            imagen,
            (x1, y1 - texto_h - 8),
            (x1 + texto_w + 4, y1),
            (0, 255, 0),
            -1,
        )
        cv2.putText(
            imagen, etiqueta, (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2,
        )

    carpeta_salida = Path(output_dir) / imagen_path.stem
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    ruta_salida = carpeta_salida / f"{imagen_path.stem}_detectado.jpg"
    cv2.imwrite(str(ruta_salida), imagen)

    return str(ruta_salida)


def main():
    parser = argparse.ArgumentParser(
        description="Deteccion de placas vehiculares con YOLOv8"
    )

    parser.add_argument(
        "--imagen",
        required=True,
        help="Ruta de la imagen a analizar"
    )

    parser.add_argument(
        "--output",
        default="resultados",
        help="Carpeta base donde se guardaran los resultados (por defecto: 'resultados')"
    )

    args = parser.parse_args()

    total_placas, resultado = detectar_placas(args.imagen)

    if total_placas > 0:
        print(f"Se detectaron {total_placas} placa(s) en la imagen.")
        ruta_guardada = dibujar_y_guardar(args.imagen, resultado, args.output)
        print(f"Imagen con bounding boxes guardada en: {ruta_guardada}")
    else:
        print("No se detecto la placa")


if __name__ == "__main__":
    main()
