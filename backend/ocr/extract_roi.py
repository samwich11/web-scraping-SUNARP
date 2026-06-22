import cv2
import json

#===============================================================
# Extraer regiones de interés (ROI) para cada campo
#===============================================================

debug = imagen_recortada.copy()

list_roi = {}

for campo in campos:
    roi = cv2.selectROI(
        f"Seleccionar ROI para {campo}",
        debug,
        showCrosshair=True,
        fromCenter=False
    )

    x, y, w, h = roi

    list_roi[campo] = {
        "x": int(x),
        "y": int(y),
        "w": int(w),
        "h": int(h)
    }

    cv2.destroyAllWindows()

with open("campos.json", "w", encoding="utf-8") as archivo:
    json.dump(list_roi, archivo, indent=4, ensure_ascii=False)

print("Coordenadas guardadas correctamente en 'campos.json'.")