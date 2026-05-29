# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time

# PLACA = "ADQ345"

# driver = webdriver.Chrome()

# try:
#     driver.get(
#         "https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio"
#     )

#     # Esperar a que cargue la página
#     placa = WebDriverWait(driver, 30).until(
#         EC.element_to_be_clickable((By.ID, "nroPlaca"))
#     )

#     # Escribir usando JavaScript
#     driver.execute_script("""
#         arguments[0].value = arguments[1];
#         arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
#         arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
#     """, placa, PLACA)

#     print("Placa ingresada.")
#     print("Resuelve el Turnstile manualmente.")

#     input("Cuando aparezca 'Operación exitosa', presiona ENTER...")

#     # Buscar todos los botones para inspeccionar
#     botones = driver.find_elements(By.TAG_NAME, "button")

#     print("\nBotones encontrados:")
#     for i, boton in enumerate(botones):
#         print(f"{i}: {boton.text}")

#     # Buscar el botón de búsqueda
#     boton_busqueda = None

#     for boton in botones:
#         texto = boton.text.strip().lower()

#         if "búsqueda" in texto or "busqueda" in texto:
#             boton_busqueda = boton
#             break

#     if boton_busqueda is None:
#         raise Exception("No se encontró el botón de búsqueda")

#     print("\nHaciendo clic en búsqueda...")

#     driver.execute_script(
#         "arguments[0].click();",
#         boton_busqueda
#     )

#     time.sleep(5)

#     # Guardar HTML
#     with open("resultado.html", "w", encoding="utf-8") as f:
#         f.write(driver.page_source)

#     print("\nHTML guardado en resultado.html")

#     # Mostrar texto visible de la página
#     print("\n=== TEXTO DE LA PÁGINA ===\n")
#     print(driver.find_element(By.TAG_NAME, "body").text)

#     input("\nPresiona ENTER para cerrar...")

# finally:
#     driver.quit()

from selenium import webdriver

driver = webdriver.Chrome()

driver.get(
    "https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio"
)

print(
    driver.execute_script(
        "return navigator.webdriver"
    )
)

input()

driver.quit()


    
"""from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()

driver.get(
    "https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio"
)

time.sleep(5)

print("Título:", driver.title)
print("URL:", driver.current_url)

inputs = driver.find_elements(By.TAG_NAME, "input")

print("Inputs encontrados:", len(inputs))

for i, inp in enumerate(inputs):
    print(i, inp.get_attribute("id"))

input("Presiona Enter para cerrar...")

driver.quit()"""
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# import time

# driver = webdriver.Chrome()

# driver.get(
#     "https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio"
# )

# time.sleep(5)

# placa = driver.find_element(By.ID, "nroPlaca")

# print("Visible:", placa.is_displayed())
# print("Enabled:", placa.is_enabled())

# print("\nHTML:")
# print(placa.get_attribute("outerHTML"))

# input("\nPresiona Enter para cerrar")

# driver.quit()