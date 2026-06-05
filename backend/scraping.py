from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from pathlib import Path
import base64

# PLACA = "ADQ345"
# PLACA = "X7I962"
PLACA = "A1B234"

options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("--disable-blink-features=AutomationControlled")   # Disable WebDriver detection
options.add_argument("--disable-extensions")                            # Disable extensions to reduce detection
options.add_argument("--no-sandbox")                                    # Disable developer mode
options.add_argument("--disable-infobars")                              # Disable "Chrome is being controlled by automated test software" infobar
options.add_argument("--disable-dev-shm-usage")                         # Disable shared memory usage to prevent crashes in some environments
options.add_argument("--disable-browser-side-navigation")               # Disable browser side navigation to prevent detection
options.add_argument("--disable-gpu")                                   # Disable GPU to reduce resource usage and potential detection
# options.add_argument("--auto-open-devtools-for-tabs")                   # Automatically open devtools for tabs

driver = webdriver.Chrome(options=options)

driver.execute_script("window.open('https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio', '_blank')")

time.sleep(15)

driver.switch_to.window(driver.window_handles[1])

# driver.switch_to.frame(0)

# driver.find_element(By.XPATH, '//*[@id="BbLB6"]/div/label/input').click()   # Marcar el checkbox de términos aceptados

input_placa = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.ID, "nroPlaca"))
)

# Comprobar el estado del input de placa
"""print("enabled:", input_placa.is_enabled())
print("displayed:", input_placa.is_displayed())
print("readonly:", input_placa.get_attribute("readonly"))
print("disabled:", input_placa.get_attribute("disabled"))"""

input_placa.clear()
input_placa.send_keys(PLACA)

# Comprobar que se escribió la placa correctamente
print("Valor:", input_placa.get_attribute("value"))

# Encontrar el checkbox de términos aceptados
# checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")

# print("Checkboxes:", len(checkboxes))

# for i, cb in enumerate(checkboxes):
#     print(i)
#     print(cb.get_attribute("outerHTML"))

btn_buscar = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(., 'Realizar Busqueda')]")
    )
)

btn_buscar.click()

img = WebDriverWait(driver, 30).until(
    EC.visibility_of_element_located(
        (
            By.XPATH, '/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/img'
        )
    )
)

# Test de atributos de la imagen y guardado de imagen
# print("width:", img.size["width"])
# print("height:", img.size["height"])

# print("size:", img.size)
# print("location:", img.location)

# src = img.get_attribute("src")
# print("src length:", len(src))

# src1 = img.get_attribute("src")

# time.sleep(3)

# src2 = img.get_attribute("src")

# print(src[:100])
# print(src1 == src2)
# print(len(src1))
# print(len(src2))

# time.sleep(7)

# Ruta
BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)    # Crear la carpeta de resultados si no existe

# Nombre archivo
archivo = RESULTS_DIR / f"{PLACA}.png"

# Obtener imagen Base64
src = img.get_attribute("src")

# Decodificar y guardar imagen original
base64_data = src.split(",", 1)[1]

with open(archivo, "wb") as f:
    f.write(base64.b64decode(base64_data))
    
print(f"Imagen guardada en: {archivo}")

# Guardar la imagen
# img.screenshot(str(archivo))

# print(f"Imagen guardada en: {archivo}")