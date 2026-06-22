import easyocr
import cv2

reader = easyocr.Reader(['en', 'es'], gpu=True)
ruta = r'C:\Users\Daniel\Documents\Tech-Lab\web scraping\backend\results\A1B234.png'
imagen = cv2.imread(ruta)
debug = imagen.copy()

CAMPOS = {
    "placa":      (190, 160, 180, 35),
    "serie":      (190, 185, 300, 35),
    "vin":        (190, 210, 300, 35),
    "motor":      (190, 238, 200, 35),
    "color":      (190, 264, 220, 35),
    "marca":      (190, 290, 180, 35),
    "modelo":     (190, 315, 180, 35),
    "vigente":    (190, 340, 180, 35),
    "anterior":   (190, 365, 180, 35),
    "estado":     (190, 390, 220, 35),
    "anotacion":  (190, 415, 220, 35),
    "sede":       (190, 440, 180, 35),
    "anio":       (190, 465, 180, 35),
    "propietario(s)": (5, 535, 530, 110)
}

datos = {}

for campo, (x, y, w, h) in CAMPOS.items():
    cv2.rectangle(
        debug,
        (x, y),
        (x + w, y + h),
        (0, 255, 0),
        2
    )

    cv2.putText(
        debug,
        campo,
        (x, y - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 255),
        1
    )

cv2.imwrite("debug_campos.png", debug)

for campo, (x,y,w,h) in CAMPOS.items():

    roi = imagen[y:y+h, x:x+w]
    
    # Escala de grises
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Aumento de tamaño
    gray = cv2.resize(
        gray,
        None,
        fx=3,
        fy=3,
        interpolation=cv2.INTER_CUBIC
    )

    # Binarización adaptativa
    th = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    texto = reader.readtext(
        th,
        detail=0,
        paragraph=True,
        decoder='beamsearch',
    )
    
    texto_propietarios = reader.readtext(
        roi,
        detail=0,
        paragraph=False,
    )

    datos[campo] = " ".join(texto)

datos["propietario(s)"] = texto_propietarios

for campo, valor in datos.items():
    print(f"{campo}: {valor}")
