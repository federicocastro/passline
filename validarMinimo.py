#!/usr/bin/env python3
import base64
import io
import os
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Configuración
NOMBRE_ARCHIVO = 'filas.txt'
UBICACION_FILAS_A_VALIDAR = 'filasAValidar'
VALOR_POSICION_ACEPTABLE_FILA = 30  # umbral de aceptabilidad (% de posición)
TIEMPO_ESPERA = 10  # segundos de timeout para la barra de progreso


def get_progress_bar_value(full_url: str, timeout: int = TIEMPO_ESPERA) -> int:
    """
    Abre Chrome, navega a `full_url`, espera hasta `timeout` segundos
    a que aparezca el elemento con ID MainPart_divProgressbar,
    y devuelve su atributo 'aria-valuenow' como entero.
    """
    driver = webdriver.Chrome()
    try:
        # driver.get(full_url)
        # wait = WebDriverWait(driver, timeout)

        # try:
        #     WebDriverWait(driver, 5).until(
        #         EC.element_to_be_clickable((By.CLASS_NAME, 'botdetect-button'))
        #     )
        # except Exception:
        #     print("EXCEPCION")
        # img_elem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'captcha-code')))
        # b64data = img_elem.get_attribute('src').split(',', 1)[1]
        # buffer = io.BytesIO(base64.b64decode(b64data))

        # codigo_captcha = obtener_texto_captcha_sync(buffer, '1')

        # input_elem = driver.find_element(By.ID, 'solution')
        # input_elem.clear()
        # input_elem.send_keys(codigo_captcha)
        # driver.find_element(By.CLASS_NAME, 'botdetect-button').click()


        # elem = wait.until(
        #     EC.presence_of_element_located((By.ID, "MainPart_divProgressbar"))
        # )
        # raw = elem.get_attribute("aria-valuenow")
        # return int(raw)
        return 50
    finally:
        driver.quit()


def guardarFilasValidadas(respuestas):
    datosProcesados = []
    datosValorNoAceptable = []
    datosFallidos = []

    for valor, filaUrl in respuestas:
        if valor is None:
            datosFallidos.append(filaUrl)
        else:
            if valor >= VALOR_POSICION_ACEPTABLE_FILA:
                datosProcesados.append((valor, filaUrl))
                print(valor, filaUrl)
            else:
                datosValorNoAceptable.append(filaUrl)

    datosProcesadosOrdenados = sorted(datosProcesados, key=lambda x: x[0], reverse=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Carpeta de respuestas aceptables
    carpeta = 'filasValidadas'
    os.makedirs(carpeta, exist_ok=True)
    if datosProcesadosOrdenados:
        ruta = os.path.join(carpeta, f'filas-{timestamp}.txt')
        with open(ruta, 'w', encoding='utf-8') as f:
            for valor, url in datosProcesadosOrdenados:
                f.write(f"{valor};{url}\n")

    # Carpeta de validaciones fallidas
    carpeta = 'validacionesFallidas'
    os.makedirs(carpeta, exist_ok=True)
    if datosFallidos:
        ruta = os.path.join(carpeta, f'filas-{timestamp}.txt')
        with open(ruta, 'w', encoding='utf-8') as f:
            for url in datosFallidos:
                f.write(f"{url}\n")

    # Carpeta de posiciones no aceptables
    carpeta = 'filasValorNoAlcanzado'
    os.makedirs(carpeta, exist_ok=True)
    if datosValorNoAceptable:
        ruta = os.path.join(carpeta, f'filas-{timestamp}.txt')
        with open(ruta, 'w', encoding='utf-8') as f:
            for url in datosValorNoAceptable:
                f.write(f"{url}\n")


def main():
    start = time.time()
    input_path = os.path.join(UBICACION_FILAS_A_VALIDAR, NOMBRE_ARCHIVO)
    if not os.path.isfile(input_path):
        print(f"❌ Archivo no encontrado: {input_path}")
        return

    respuestas = []
    with open(input_path, 'r', encoding='utf-8') as file:
        for line in file:
            url = line.strip()
            if not url:
                continue
            print(f"Procesando: {url}")
            try:
                valor = get_progress_bar_value(url)
                respuestas.append((valor, url))
                print(f" → {valor}%")
            except Exception as e:
                print(f"[ERROR] {url}: {e}")
                respuestas.append((None, url))

    guardarFilasValidadas(respuestas)
    elapsed = time.time() - start
    print(f"Proceso completado en {elapsed:.2f} segundos.")


if __name__ == '__main__':
    main()
