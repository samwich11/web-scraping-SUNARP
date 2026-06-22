import torch

#===============================================================
# Comprobar la disponibilidad de CUDA - uso de GPU para procesamiento de OCR
#=============================================================== 

print("Versión:", torch.__version__)
print("CUDA incluida:", torch.version.cuda)
print("CUDA disponible:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))