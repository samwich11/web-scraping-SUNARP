from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import base64
import time


# ===============================================================
# Rutas base
# ===============================================================

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ===============================================================
# Configuración del navegador
# ===============================================================

def create_driver():
    """
    Crea y configura el driver de Chrome.
    """

    options = webdriver.ChromeOptions()

    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    return driver


# ===============================================================
# Scraping principal
# ===============================================================

def scrape_vehicle_image(placa: str, close_driver: bool = True) -> Path:
    """
    Consulta la placa en SUNARP, obtiene la imagen resultado y la guarda en backend/results.

    Retorna:
        Path de la imagen descargada.
    """

    placa = placa.upper().strip()

    driver = create_driver()

    try:
        url = "https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio"

        print(f"Abriendo página de SUNARP para placa: {placa}")

        driver.get(url)

        wait = WebDriverWait(driver, 60)

        # Esperar input de placa
        input_placa = wait.until(
            EC.element_to_be_clickable((By.ID, "nroPlaca"))
        )

        input_placa.clear()
        input_placa.send_keys(placa)

        print("Valor ingresado:", input_placa.get_attribute("value"))

        # Pausa por si aparece Cloudflare Turnstile
        print("\nSi aparece Cloudflare Turnstile, resuélvelo manualmente.")
        input("Cuando la página esté lista, presiona ENTER para continuar...")

        # Click en botón buscar
        btn_buscar = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Realizar Busqueda')]")
            )
        )

        btn_buscar.click()

        # btn_buscar = WebDriverWait(driver, 30).until(
        #     EC.element_to_be_clickable(
        #         (By.XPATH, "//button[contains(., 'Realizar Busqueda')]")
        #     )
        # )

        # btn_buscar.click()

        print("Búsqueda enviada. Esperando imagen resultado...")

        # Esperar imagen resultado
        img = wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/img"
                )
            )
        )

        # Espera adicional para asegurar que el src base64 cargue completo
        time.sleep(3)

        src = img.get_attribute("src")

        if not src:
            raise ValueError("No se encontró el atributo src en la imagen.")

        if "," not in src:
            raise ValueError(f"El src no tiene formato Base64 válido: {src[:100]}")

        base64_data = src.split(",", 1)[1]

        image_path = RESULTS_DIR / f"{placa}.png"

        with open(image_path, "wb") as file:
            file.write(base64.b64decode(base64_data))

        print(f"Imagen guardada en: {image_path}")

        return image_path

    finally:
        if close_driver:
            driver.quit()


# ===============================================================
# Ejecución directa
# ===============================================================

if __name__ == "__main__":
    scrape_vehicle_image("A1B234")