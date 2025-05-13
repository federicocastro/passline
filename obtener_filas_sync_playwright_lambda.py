import base64
import io
import os
import boto3
from uuid import uuid4
from time import sleep
from PIL import Image
from playwright.sync_api import sync_playwright
from openai import OpenAI
from dotenv import load_dotenv

# DynamoDB config
dynamo = boto3.resource('dynamodb', region_name='us-east-1')
tabla = dynamo.Table('FilasQueue')

load_dotenv()

# Parámetros globales
ANCHO_A_CORTAR = 50
RGB_NEGRO = (0, 0, 0)
RGB_BLANCO = (255, 255, 255)
URL = os.environ.get("URL", "https://dfentertainment.queue-it.net/?c=dfentertainment&e=badbonnyprever&cid=es-CL")
TIMEOUT = 20000  # en milisegundos para Playwright

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAIAPI_KEY"))

# Directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = "/tmp/images"
RESULTS_DIR = "/tmp/results"
DEBUG=os.getenv("DEBUG", False)
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
    print(f"[Task {id_tarea}] Iniciando navegador con Playwright...")

    fila_id = None
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--single-process',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ]
        )
        context = browser.new_context(viewport={"width":1200, "height":800})
        page = context.new_page()

        print(f"[Task {id_tarea}] Accediendo a URL: {URL}")
        page.goto(URL, timeout=TIMEOUT)

        ultimo_src_captcha = None

        for intento in range(6):
            print(f"[Task {id_tarea}] Intento de captcha #{intento + 1}")

            try:
                page.wait_for_selector('.botdetect-button', timeout=5000)
            except Exception:
                print(f"[Task {id_tarea}] Botón captcha no encontrado, probablemente no necesario")
                break

            page.wait_for_selector('.captcha-code', timeout=TIMEOUT)
            src_captcha = page.get_attribute('.captcha-code', 'src')

            if src_captcha == ultimo_src_captcha:
                print(f"[Task {id_tarea}] La imagen del captcha no cambió, esperando...")
                sleep(2)
                continue
            ultimo_src_captcha = src_captcha

            b64data = src_captcha.split(',', 1)[1]
            buffer = io.BytesIO(base64.b64decode(b64data))
            print(f"[Task {id_tarea}] Captcha descargado")

            codigo_captcha = obtener_texto_captcha(buffer, id_tarea)

            page.fill('#solution', codigo_captcha)
            page.click('.botdetect-button')
            print(f"[Task {id_tarea}] Captcha enviado: {codigo_captcha}")

            sleep(3)

        sleep(6)
        fila_elem = page.wait_for_selector('#hlLinkToQueueTicket2', timeout=TIMEOUT)
        fila_id = fila_elem.inner_text().strip()
        print(f"[Task {id_tarea}] ID de fila obtenido: {fila_id}")
        context.close()
        browser.close()

       # Guardar en DynamoDB si tiene fila_id
        if fila_id and fila_id != '00000000-0000-0000-0000-000000000000':
            tabla.put_item(
                Item={
                    'task_id': id_tarea,
                    'fila_id': fila_id
                }
            )

    return fila_id

def main():
    task_id = f"{uuid4().hex}"
    print(f"\n🔹 Iniciando tarea {task_id}")
    fila_id = ejecutar_navegador_sync(task_id)
    print(f"[Task {task_id}] Resultado final - ID de fila: {fila_id}")

if __name__ == "__main__":
    main()
