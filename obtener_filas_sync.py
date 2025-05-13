import base64
import io
import os
from uuid import uuid4
from time import sleep
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Parámetros globales
ANCHO_A_CORTAR = 50
RGB_NEGRO = (0, 0, 0)
RGB_BLANCO = (255, 255, 255)
URL = 'https://dfentertainment.queue-it.net/?c=dfentertainment&e=badbonnyprever&cid=es-CL'
TIMEOUT = 20

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAIAPI_KEY"))

# Directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def obtener_texto_captcha(buffer_imagen, id_tarea) -> str:
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

    local_path = os.path.join(IMAGES_DIR, f"{uuid4().hex}.png")
    imagen_modificada.save(local_path)
    print(f"[Task {id_tarea}] Imagen captcha procesada guardada: {local_path}")

    buffer_final = io.BytesIO()
    imagen_modificada.save(buffer_final, format="PNG")
    buffer_final.seek(0)
    image_b64 = base64.b64encode(buffer_final.read()).decode('utf-8')

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extrae solo el texto que aparece en esta imagen, sin explicaciones."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=20
    )

    texto = response.choices[0].message.content.upper().strip()
    print(f"[Task {id_tarea}] Captcha reconocido: {texto}")

    return texto

def ejecutar_navegador_sync(id_tarea):
    print(f"[Task {id_tarea}] Iniciando navegador...")
    opts = Options()
    #opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1200,800")

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, TIMEOUT)
    fila_id = None

    try:
        print(f"[Task {id_tarea}] Accediendo a URL: {URL}")
        driver.get(URL)

        ultimo_src_captcha = None

        for intento in range(6):
            print(f"[Task {id_tarea}] Intento de captcha #{intento + 1}")

            sleep(1)
            try:
                wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'botdetect-button')))
            except Exception:
                print(f"[Task {id_tarea}] Botón captcha no encontrado, probablemente no necesario")
                break

            def cambio_de_captcha(driver):
                elem = driver.find_element(By.CLASS_NAME, 'captcha-code')
                src = elem.get_attribute('src')
                return src if src != ultimo_src_captcha else False

            src_captcha = WebDriverWait(driver, TIMEOUT).until(cambio_de_captcha)
            ultimo_src_captcha = src_captcha

            b64data = src_captcha.split(',', 1)[1]
            buffer = io.BytesIO(base64.b64decode(b64data))
            print(f"[Task {id_tarea}] Captcha descargado")

            codigo_captcha = obtener_texto_captcha(buffer, id_tarea)

            input_elem = driver.find_element(By.ID, 'solution')
            input_elem.clear()
            input_elem.send_keys(codigo_captcha)
            driver.find_element(By.CLASS_NAME, 'botdetect-button').click()
            print(f"[Task {id_tarea}] Captcha enviado: {codigo_captcha}")

            sleep(3)

        sleep(6)
        fila_elem = wait.until(EC.presence_of_element_located((By.ID, 'hlLinkToQueueTicket2')))
        fila_id = fila_elem.text.strip()
        print(f"[Task {id_tarea}] ID de fila obtenido: {fila_id}")

        # Guardamos la fila obtenida en un archivo txt
        ruta_resultado = os.path.join(RESULTS_DIR, f"id_{id_tarea}_{fila_id}.txt")
        with open(ruta_resultado, "w") as archivo_resultado:
            archivo_resultado.write(fila_id)

        print(f"[Task {id_tarea}] Fila guardada en: {ruta_resultado}")

    except Exception as e:
        print(f"[Task {id_tarea}] Error durante ejecución: {e}")
    finally:
        driver.quit()
        print(f"[Task {id_tarea}] Navegador cerrado")

    return fila_id

def main():
    task_id = uuid4()
    print(f"\n🔹 Iniciando tarea {task_id}")
    fila_id = ejecutar_navegador_sync(task_id)
    print(f"[Task: task_id] Resultado final - ID de fila: {fila_id}")

if __name__ == "__main__":
    main()
