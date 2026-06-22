import cv2

#===============================================================
# Eliminar marca de agua y recortar encabezado
#=============================================================== 
ruta = r'C:\Users\Daniel\Documents\Tech-Lab\web scraping\backend\results\ADQ345_.png'

# Escala de grises
imagen = cv2.imread(ruta, cv2.COLOR_BGR2GRAY)

if imagen is None:
    raise FileNotFoundError(f'No se pudo cargar la imagen: {ruta}')

# Binarización
_, imagen_limpia = cv2.threshold(imagen, 150, 255, cv2.THRESH_BINARY)

# Guardar imagen sin marca de agua
cv2.imwrite('imagen_sin_marca.png', imagen_limpia)

# print("Imagen procesada y guardada como 'imagen_sin_marca.png'.")

# Obtener dimensiones de la imagen
alto, ancho = imagen_limpia.shape[:2]

# Recortar encabezado
x_inicio = 0
y_inicio = 140      # Elimina el encabezado
x_fin = ancho
y_fin = alto

imagen_recortada = imagen_limpia[y_inicio:y_fin, x_inicio:x_fin]

# Guardar imagen recortada
cv2.imwrite('imagen_recortada.png', imagen_recortada)

if __name__ == "__main__":
    print("Preprocesamiento completado. Imagen recortada guardada como 'imagen_recortada.png'.")
    # Imprimir información de la imagen recortada
    print("Imagen recortada y guardada como 'imagen_recortada.png'.")
    print(f"Dimensiones originales: {ancho}x{alto}")
    print(f"Dimensiones recortadas: {imagen_recortada.shape}")
    print(f"Dimensiones recortadas: {imagen_recortada.shape[1]}x{imagen_recortada.shape[0]}")