import asyncio
import base64
import io
import os
from uuid import uuid4
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from git_batch_manager import GitBatchManager
import pathlib

load_dotenv()

ANCHO_A_CORTAR = 50
RGB_NEGRO = (0, 0, 0)
RGB_BLANCO = (255, 255, 255)
URL = 'https://dfentertainment.queue-it.net/?c=dfentertainment&e=badbonnyprever&cid=es-CL'
TIMEOUT = 15

client = OpenAI(api_key=os.getenv("OPENAIAPI_KEY"))

MAX_BROWSERS = 5
webdriver_executor = ThreadPoolExecutor(max_workers=MAX_BROWSERS)

BASE_DIR = pathlib.Path(__file__).parent

os.makedirs(BASE_DIR / "images", exist_ok=True)
os.makedirs(BASE_DIR / "uploaded_images", exist_ok=True)

batch_manager = GitBatchManager(BASE_DIR/ "uploaded_images")


async def subir_imagen(buffer, id_tarea):
    unique_name = f"{uuid4().hex}.png"
    local_path = BASE_DIR / f"images/{unique_name}"

    with open(local_path, 'wb') as f:
        f.write(buffer.getvalue())

    print(f"[Task {id_tarea}] Imagen guardada localmente: {local_path}")

    # Ahora sí coincide exactamente con la URL generada por el batch_manager
    url, future = await batch_manager.add_image(local_path)
    print(f"[Task {id_tarea}] URL prometida: {url}")

    await future
    print(f"[Task {id_tarea}] Imagen subida correctamente: {url}")

    return url


async def obtener_texto_captcha(buffer_imagen, id_tarea) -> str:
    print(f"[Task {id_tarea}] Procesando imagen captcha...")
    imagen_original = Image.open(buffer_imagen).convert("RGB")
    pixeles = imagen_original.load()
    ancho, alto = imagen_original.size
    imagen_modificada = Image.new("RGB", (ancho - ANCHO_A_CORTAR * 2, alto))

    primer_pixel = pixeles[0, 0]
    tipo = "CUADRICULADO" if primer_pixel == (235, 235, 235) else ("CELESTE" if primer_pixel[0] > 130 else "AZUL")
    print(f"[Task {id_tarea}] Tipo captcha detectado: {tipo}")

    for x in range(ANCHO_A_CORTAR, ancho - ANCHO_A_CORTAR):
        for y in range(alto):
            r, g, b = pixeles[x, y]
            cond = (85 <= r <= 125 and 85 <= g <= 125 and b <= 140) or \
                   (r > 200 and g > 200) if tipo == "CUADRICULADO" else \
                   (r < 100 and g < 130 if tipo == "AZUL" else r > 130)
            imagen_modificada.putpixel((x - ANCHO_A_CORTAR, y), RGB_NEGRO if cond else RGB_BLANCO)

    buffer_final = io.BytesIO()
    imagen_modificada.save(buffer_final, format="PNG")
    buffer_final.seek(0)

    # Usa ahora el método correcto y compatible con batch manager
    url_imagen = await subir_imagen(buffer_final, id_tarea)

    print(f"[Task {id_tarea}] Consultando OpenAI...")
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "user", "content": "Extrae solo el texto que aparece en esta imagen, sin explicaciones."},
            {"role": "user", "content": [{"type": "input_image", "image_url": url_imagen}]}
        ]
    )

    texto = response.output_text.upper().strip()
    print(f"[Task {id_tarea}] Captcha reconocido: {texto}")

    return texto

async def ejecutar_navegador_async(id_tarea):
    print(f"[Task {id_tarea}] Iniciando navegador...")
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1200,800")

    loop = asyncio.get_event_loop()

    # Inicia Selenium en thread aparte
    def iniciar_driver():
        driver = webdriver.Chrome(options=opts)
        return driver

    driver = await loop.run_in_executor(webdriver_executor, iniciar_driver)
    wait = WebDriverWait(driver, TIMEOUT)
    fila_id = None

    try:
        print(f"[Task {id_tarea}] Accediendo a URL: {URL}")
        driver.get(URL)

        last_captcha_src = None  # Guarda el captcha anterior para detectar cambios

        for intento in range(2):
            print(f"[Task {id_tarea}] Intento de captcha #{intento+1}")

            # Espera botón captcha
            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'botdetect-button'))
                )
            except Exception:
                print(f"[Task {id_tarea}] No se encontró botón captcha, probablemente no necesario")
                break

            # Espera que la imagen captcha sea nueva y no la anterior
            def captcha_src_cambio(driver):
                elem = driver.find_element(By.CLASS_NAME, 'captcha-code')
                src = elem.get_attribute('src')
                return src if src != last_captcha_src else False

            img_elem = WebDriverWait(driver, TIMEOUT).until(captcha_src_cambio)
            last_captcha_src = img_elem  # Actualiza con el nuevo captcha src

            # Ahora sí, descarga la imagen captcha nueva
            b64data = last_captcha_src.split(',', 1)[1]
            buffer = io.BytesIO(base64.b64decode(b64data))
            print(f"[Task {id_tarea}] Captcha descargado desde navegador")

            # Procesa el captcha de manera asincrónica
            codigo_captcha = await obtener_texto_captcha(buffer, id_tarea)

            # Envía solución al navegador abierto
            input_elem = driver.find_element(By.ID, 'solution')
            input_elem.clear()
            input_elem.send_keys(codigo_captcha)
            driver.find_element(By.CLASS_NAME, 'botdetect-button').click()
            print(f"[Task {id_tarea}] Captcha enviado: {codigo_captcha}")

            # Espera corta tras enviar solución, para que la página recargue captcha o pase a fila
            await asyncio.sleep(3)

        # Espera a obtener la ID de fila
        await asyncio.sleep(5)
        fila_elem = wait.until(EC.presence_of_element_located((By.ID, 'hlLinkToQueueTicket2')))
        fila_id = fila_elem.text.strip()
        print(f"[Task {id_tarea}] ID de fila obtenido: {fila_id}")

    except Exception as e:
        print(f"[Task {id_tarea}] Error durante ejecución: {e}")
    finally:
        driver.quit()
        print(f"[Task {id_tarea}] Navegador cerrado")

    return fila_id

async def obtener_fila_id_async(id_tarea):
    fila_id = await ejecutar_navegador_async(id_tarea)
    print(f"[Task {id_tarea}] Resultado final - ID de fila: {fila_id}")


async def main(cantidad_ids):
    await batch_manager.start()
    tareas = [obtener_fila_id_async(i) for i in range(cantidad_ids)]
    await asyncio.gather(*tareas)
    await batch_manager.stop()


if __name__ == "__main__":
    asyncio.run(main(1))
