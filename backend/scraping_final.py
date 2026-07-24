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

        # Replicar el flujo de scraping.py: abrir la consulta en una pestaña
        # nueva y darle tiempo al captcha invisible para validarse.
        driver.execute_script("window.open(arguments[0], '_blank')", url)

        WebDriverWait(driver, 10).until(
            lambda current_driver: len(current_driver.window_handles) > 1
        )
        driver.switch_to.window(driver.window_handles[-1])

        time.sleep(15)

        wait = WebDriverWait(driver, 60)

        # Esperar input de placa
        input_placa = wait.until(
            EC.element_to_be_clickable((By.ID, "nroPlaca"))
        )

        input_placa.clear()
        input_placa.send_keys(placa)

        print("Valor ingresado:", input_placa.get_attribute("value"))

        # Esperar y pulsar el botón automáticamente, sin intervención manual.
        btn_buscar = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Realizar Busqueda')]")
            )
        )

        btn_buscar.click()

        print("Búsqueda enviada. Esperando imagen resultado...")

        image_locator = (
            By.XPATH,
            "/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/img"
        )
        captcha_error_locator = (By.ID, "swal2-title")

        # Finalizar inmediatamente si SUNARP rechaza el captcha, en lugar de
        # agotar el tiempo esperando una imagen que no será generada.
        result = WebDriverWait(driver, 30).until(
            EC.any_of(
                EC.visibility_of_element_located(image_locator),
                EC.visibility_of_element_located(captcha_error_locator),
            )
        )

        if result.get_attribute("id") == "swal2-title":
            detail_elements = driver.find_elements(By.ID, "swal2-html-container")
            detail = detail_elements[0].text.strip() if detail_elements else ""
            message = result.text.strip() or "Captcha rechazado por SUNARP"
            if detail:
                message = f"{message}: {detail}"
            raise RuntimeError(message)

        img = result

        # Esperar hasta que Angular termine de colocar la imagen en Base64.
        src = wait.until(
            lambda _driver: (
                img.get_attribute("src")
                if (img.get_attribute("src") or "").startswith("data:image/")
                and "," in (img.get_attribute("src") or "")
                else False
            )
        )

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
    scrape_vehicle_image("5367MC")
