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
from text import subir_imagen_y_obtener_url

ANCHO_A_CORTAR = 50
RGB_NEGRO = (0, 0, 0)
RGB_BLANCO = (255, 255, 255)
URL = 'https://dfentertainment.queue-it.net/?c=dfentertainment&e=badbonnyprever&cid=es-CL'
TIMEOUT = 15

client = OpenAI(api_key='')

MAX_BROWSERS = 5
webdriver_executor = ThreadPoolExecutor(max_workers=MAX_BROWSERS)

from git_batch_manager import GitBatchManager
import asyncio

batch_manager = GitBatchManager('/ruta/a/tu/repo')
os.makedirs("images", exist_ok=True)

async def subir_imagen(buffer, id_tarea):
    local_path = f"images/{uuid4().hex}.png"
    with open(local_path, 'wb') as f:
        f.write(buffer.getvalue())
    print(f"[Task {id_tarea}] Imagen guardada localmente: {local_path}")

    url, future = await batch_manager.add_image(local_path)
    print(f"[Task {id_tarea}] URL prometida: {url}")

    await future  # Espera que git push se complete
    print(f"[Task {id_tarea}] Imagen subida correctamente: {url}")

    return url

def obtener_texto_captcha_sync(buffer_imagen, id_tarea) -> str:
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

    uuid_imagen = uuid4()
    local_path = os.path.abspath(f"images/{uuid_imagen}.png")
    imagen_modificada.save(local_path)
    print(f"[Task {id_tarea}] Imagen captcha guardada: {local_path}")

    print(f"[Task {id_tarea}] Subiendo imagen...")
    url = subir_imagen_y_obtener_url(local_path)
    print(f"[Task {id_tarea}] Imagen subida URL: {url}")

    print(f"[Task {id_tarea}] Consultando OpenAI...")
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "user", "content": "Extrae solo el texto que aparece en esta imagen, sin explicaciones."},
            {"role": "user", "content": [{"type": "input_image", "image_url": url}]}
        ]
    )

    texto = response.output_text.upper().strip()
    print(f"[Task {id_tarea}] Captcha reconocido: {texto}")

    return texto

def ejecutar_navegador_sync(id_tarea):
    print(f"[Task {id_tarea}] Iniciando navegador...")
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1200,800")

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, TIMEOUT)
    fila_id = None

    try:
        print(f"[Task {id_tarea}] Accediendo a URL: {URL}")
        driver.get(URL)

        for intento in range(2):
            print(f"[Task {id_tarea}] Intento de captcha #{intento+1}")
            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'botdetect-button'))
                )
            except Exception:
                print(f"[Task {id_tarea}] No se encontró botón captcha, probablemente no necesario")
                break

            img_elem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'captcha-code')))
            b64data = img_elem.get_attribute('src').split(',', 1)[1]
            buffer = io.BytesIO(base64.b64decode(b64data))
            print(f"[Task {id_tarea}] Captcha descargado desde navegador")

            codigo_captcha = obtener_texto_captcha_sync(buffer, id_tarea)

            input_elem = driver.find_element(By.ID, 'solution')
            input_elem.clear()
            input_elem.send_keys(codigo_captcha)
            driver.find_element(By.CLASS_NAME, 'botdetect-button').click()
            print(f"[Task {id_tarea}] Captcha enviado: {codigo_captcha}")

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
    loop = asyncio.get_event_loop()
    fila_id = await loop.run_in_executor(webdriver_executor, ejecutar_navegador_sync, id_tarea)
    print(f"[Task {id_tarea}] Resultado final - ID de fila: {fila_id}")

async def main(cantidad_ids):
    tareas = [obtener_fila_id_async(i) for i in range(cantidad_ids)]
    await asyncio.gather(*tareas)

if __name__ == "__main__":
    asyncio.run(main(5))
