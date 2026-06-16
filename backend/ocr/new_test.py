import cv2
import easyocr

ruta = r'C:\Users\Daniel\Documents\Tech-Lab\web scraping\backend\results\ADQ345_3.png'

imagen = cv2.imread(ruta, cv2.COLOR_BGR2GRAY)

if imagen is None:
    raise FileNotFoundError(f'No se pudo cargar la imagen: {ruta}')

_, imagen_limpia = cv2.threshold(imagen, 150, 255, cv2.THRESH_BINARY)

cv2.imwrite('imagen_sin_marca.png', imagen_limpia)

reader = easyocr.Reader(['en', 'es'], gpu=True)
resultado = reader.readtext(imagen_limpia)

for bbox, texto, prob in resultado:
    # print(f"Texto: {texto} (Confianza: {prob:.2f})")
    # print(f"Coordenadas: {bbox}\n")
    print(texto)
    print("-" * 40)