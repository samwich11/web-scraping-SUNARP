import json
import cv2
import easyocr

ruta = r'C:\Users\Daniel\Documents\Tech-Lab\web scraping\backend\results\A1B234.png'

campos = [
    "placa",          
    "serie",          
    "vin",            
    "motor",          
    "color",          
    "marca",          
    "modelo",         
    "placa_vigente",  
    "placa_anterior", 
    "estado",         
    "anotaciones",    
    "sede",           
    "anio_modelo",    
    "propietario",    
]



cv2.imwrite("debug_campos.png", debug)
cv2.imshow("ROI", debug)

print("Imagen de depuración guardada como 'debug_campos.png'.")

# cv2.imwrite('imagen_recortada.png', imagen_recortada)

# reader = easyocr.Reader(['en', 'es'], gpu=True)
# resultado = reader.readtext(imagen_limpia)

# for bbox, texto, prob in resultado:
    # print(f"Texto: {texto} (Confianza: {prob:.2f})")
    # print(f"Coordenadas: {bbox}\n")
    # print(texto)
    # print("-" * 40)
    # pass