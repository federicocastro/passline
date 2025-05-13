# test_fila_simple.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
def get_progress_bar_value(url: str, timeout: int = 20) -> int:
    """
    Abre Chrome, navega a `url`, espera hasta `timeout` segundos
    a que aparezca el elemento con ID MainPart_divProgressbar,
    y devuelve su atributo 'aria-valuenow' como entero.
    """
    # Asegúrate de tener chromedriver en tu PATH
    driver = webdriver.Chrome()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, timeout)
        time.sleep(3)
        elem = wait.until(
            EC.presence_of_element_located((By.ID, "MainPart_divProgressbar"))
        )
        print(elem)
        raw = elem.get_attribute("aria-valuenow") or "0"
        return int(raw)
    finally:
        driver.quit()

if __name__ == "__main__":
    url = input("→ Ingresa la URL completa a testear: ").strip()
    try:
        valor = get_progress_bar_value(url)
        print(f"Valor de la posición en fila (porcentaje): {valor}%")
    except Exception as e:
        print(f"❌ Error al obtener el valor: {e}")
