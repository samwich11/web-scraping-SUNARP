# Web Scraping SUNARP y reconocimiento de placas

Sistema en Python para detectar placas vehiculares en imágenes, leerlas mediante OCR y consultar la información pública disponible en la plataforma de Consulta Vehicular de SUNARP.

El proyecto combina:

- **YOLOv8** para detectar placas en imágenes.
- **EasyOCR** para reconocer el número de placa.
- **Selenium** para automatizar la consulta vehicular en SUNARP.
- **OpenCV** para preprocesar las fichas obtenidas y aplicar regiones de interés (ROI).
- **JSON** para almacenar los datos extraídos y los reportes de pruebas.

> El frontend incluido es un prototipo visual. Actualmente no está conectado al pipeline de Python.

## Flujo del sistema

```text
Imagen del vehículo
        ↓
Detección de placa con YOLO
        ↓
Lectura de placa con EasyOCR
        ↓
Consulta automatizada en SUNARP
        ↓
Preprocesamiento y OCR de la ficha
        ↓
Resultados en JSON
```

También es posible omitir la detección inicial y consultar directamente una placa conocida.

## Requisitos

- Windows 10 u 11.
- Python 3.10 o superior.
- Google Chrome instalado.
- Conexión a Internet.
- Git Bash, PowerShell o una terminal equivalente.

El uso de GPU es opcional. EasyOCR puede ejecutarse con CPU, aunque el procesamiento será más lento.

## Instalación

Clona el repositorio y entra en la carpeta del proyecto:

```bash
git clone https://github.com/samwich11/web-scraping-SUNARP.git
cd "web-scraping-SUNARP"
```

Crea el entorno virtual:

```bash
python -m venv backend/.venv
```

Actívalo desde Git Bash:

```bash
source backend/.venv/Scripts/activate
```

En PowerShell:

```powershell
backend\.venv\Scripts\Activate.ps1
```

Instala las dependencias del proyecto:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Cuando el entorno esté activo aparecerá `(.venv)` al inicio de la terminal.

## Uso

Todos los comandos siguientes deben ejecutarse desde la raíz del repositorio.

### Consultar una placa

Ejecuta el pipeline de scraping, preprocesamiento, OCR y generación de JSON:

```bash
python backend/main.py 5367MC
```

Sustituye `5367MC` por la placa que quieras consultar.

Opciones disponibles:

```bash
python backend/main.py 5367MC --gpu
python backend/main.py 5367MC --no-debug-rois
python backend/main.py 5367MC --historico
```

- `--gpu`: utiliza GPU en EasyOCR si está disponible.
- `--no-debug-rois`: no guarda imágenes de depuración de los ROI.
- `--historico`: agrega una nueva consulta al JSON global sin reemplazar el registro anterior de la placa.

Si no quieres activar el entorno virtual, en Git Bash puedes ejecutar:

```bash
./backend/.venv/Scripts/python.exe backend/main.py 5367MC
```

### Probar todas las placas del JSON

Las placas de prueba se encuentran en `backend/placas_prueba.json`:

```json
{
    "placas": [
        "CKF095",
        "CUI503",
        "A8U654"
    ]
}
```

Para ejecutar todas las pruebas:

```bash
python backend/probar_placas.py
```

El proceso espera 20 segundos entre consultas, continúa cuando una placa falla y actualiza el reporte después de cada intento.

Comandos útiles:

```bash
# Procesar solo las primeras dos placas
python backend/probar_placas.py --limite 2

# Reanudar el lote desde una placa
python backend/probar_placas.py --desde BUD370

# Cambiar la espera entre consultas a 30 segundos
python backend/probar_placas.py --espera 30

# Utilizar otro archivo de placas
python backend/probar_placas.py --archivo ruta/otras_placas.json
```

Puedes detener el lote con `Ctrl+C`. El progreso procesado hasta ese momento permanecerá guardado en el reporte.

### Ejecutar el sistema ALPR completo

Para detectar y leer una placa desde una imagen antes de consultar SUNARP:

```bash
python sistema-ALRP.py --imagen "CNR-532.jpg"
```

Opciones adicionales:

```bash
python sistema-ALRP.py --imagen "CNR-532.jpg" --debug
python sistema-ALRP.py --imagen "CNR-532.jpg" --output resultados
```

### Ejecutar componentes por separado

Solo detección YOLO:

```bash
python modelo-YOLO/main.py --imagen "CNR-532.jpg"
```

Solo reconocimiento de texto con EasyOCR:

```bash
python modelo-OCR/main.py --imagen "CNR-532.jpg"
```

Con GPU:

```bash
python modelo-OCR/main.py --imagen "CNR-532.jpg" --gpu
```

## Resultados

El pipeline genera archivos en las siguientes ubicaciones:

```text
backend/results/
└── PLACA.png                         # Ficha original obtenida de SUNARP

backend/ocr/results/
├── PLACA_preprocessed.png            # Ficha normalizada y procesada
├── debug_fixed_rois.png              # Vista de los ROI
└── debug_rois/                        # Recortes individuales por campo

backend/ocr/json/
├── placas/PLACA.json                 # Resultado individual
├── vehiculos.json                    # Registro global
└── reporte_pruebas.json              # Resumen del procesamiento por lotes
```

Las capturas de SUNARP se normalizan antes del OCR para conservar la posición de los campos respecto a los ROI definidos en `backend/ocr/rois.json`.

## Estructura principal

```text
web-scraping-SUNARP/
├── backend/
│   ├── main.py                       # Pipeline para una placa conocida
│   ├── scraping_final.py             # Automatización de SUNARP
│   ├── probar_placas.py              # Ejecución por lotes
│   ├── placas_prueba.json             # Placas usadas en pruebas
│   └── ocr/
│       ├── preprocess.py              # Normalización de la ficha
│       ├── read_image.py              # OCR y generación de JSON
│       ├── create_roi.py              # Creación y visualización de ROI
│       └── rois.json                  # Coordenadas de los campos
├── modelo-YOLO/
│   ├── main.py                        # Detección de placas
│   └── modelo-deteccion-placasv3-last.pt
├── modelo-OCR/
│   └── main.py                        # Lectura de placas
├── frontend/                          # Prototipo de interfaz
├── sistema-ALRP.py                    # Flujo completo desde una imagen
└── requirements.txt
```

## Captcha y disponibilidad de SUNARP

La validación del captcha pertenece a SUNARP y puede fallar de manera intermitente por la conexión, la sesión del navegador o los mecanismos de protección del sitio. Algunos mensajes posibles son:

- `Captcha no resuelto`.
- `Error (URL) no identificado al generar el captcha`.

El scraper detecta el rechazo y detiene esa consulta para evitar esperar una imagen que no será generada. En las pruebas por lotes, el error se registra y el proceso continúa con la siguiente placa.

El proyecto no intenta evadir ni desactivar las medidas de seguridad de SUNARP.

## Consideraciones sobre los datos

Los JSON generados pueden contener información vehicular y datos personales obtenidos de SUNARP. Comparte estos archivos únicamente con personas autorizadas y de acuerdo con las normas aplicables.

## Estado del frontend

La carpeta `frontend/` contiene una interfaz estática para visualizar un dashboard, cargar archivos y mostrar placas detectadas. Por ahora sus datos son demostrativos y todavía requiere una API para comunicarse con el pipeline de Python.

