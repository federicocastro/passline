import asyncio
import base64
from enum import Enum
import io
import random
import re
import time
from PIL import Image
import pytesseract
from selenium.webdriver.common.by import By
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # PARA WINDOWS

CARPETA = 'captchas'
ANCHO_A_CORTAR = 50
RGB_NEGRO = (0, 0, 0)
RGB_BLANCO = (255, 255, 255)
CUADRICULA_GRIS = ()

class TipoDeCaptcha(Enum):
    CUADRICULADO = (235, 235, 235)  # Los RGB son iguales a estos valores
    CELESTE = (130, 130, 180)  # Los RGB son mayores a estos valores
    AZUL = (100, 100, 130)  # Los RGB son menores a estos valores

# async def validarCaptchaSoftblock(driver_url, session):
#     imagenCaptcha = await asynchronous.find_element(driver_url, session, By.CLASS_NAME, 'captcha-code')
#     if 'no such element' not in imagenCaptcha:
#         src = await asynchronous.get_attribute(driver_url, session, imagenCaptcha, 'src')
#         datos = base64.b64decode(src.split(",")[1])
#         archivoMemoria = io.BytesIO(datos)
#         texto = obtenerTextoCaptcha(archivoMemoria)
#         inputSolucionCaptcha = await asynchronous.find_element(driver_url, session, By.ID, 'solution')
#         await human_type(driver_url, session, inputSolucionCaptcha, texto)
#         botonCaptcha = await asynchronous.find_element(driver_url, session, By.CLASS_NAME, 'botdetect-button')
#         #await asyncio.sleep(1)
#         await asynchronous.click(driver_url, session, botonCaptcha)
#         await asyncio.sleep(4)

def contiene_caracteres_especiales(texto):
    # Utilizamos una expresión regular para buscar caracteres distintos de letras y números.
    # Si encuentra algún carácter especial, retorna True, de lo contrario, retorna False.
    return bool(re.search(r'[^A-Za-z0-9]', texto))

def obtenerTextoCaptcha(ruta_imagen):
    imagen_original = Image.open(ruta_imagen)
    imagen_original = imagen_original.convert("RGB")

    pixeles = imagen_original.load()
    ancho, alto = imagen_original.size

    imagen_modificada = Image.new("RGB", (ancho - ANCHO_A_CORTAR * 2, alto))

    tipoDeCaptcha = None

    primerPixel = pixeles[0, 0]

    if primerPixel == TipoDeCaptcha.CUADRICULADO.value:
        tipoDeCaptcha = TipoDeCaptcha.CUADRICULADO
    elif primerPixel[0] > TipoDeCaptcha.CELESTE.value[0] and primerPixel[1] > TipoDeCaptcha.CELESTE.value[1]:
        tipoDeCaptcha = TipoDeCaptcha.CELESTE
    else:
        tipoDeCaptcha = TipoDeCaptcha.AZUL

    for x in range(ANCHO_A_CORTAR, ancho - ANCHO_A_CORTAR):
        for y in range(alto):
            r, g, b = pixeles[x, y]

            if tipoDeCaptcha == TipoDeCaptcha.CUADRICULADO:
                if r in range(85, 125) and g in range(85, 125) and b in range(85, 140) or r > 200 and g > 200:
                    imagen_modificada.putpixel((x - ANCHO_A_CORTAR, y), RGB_NEGRO)
                else:
                    imagen_modificada.putpixel((x - ANCHO_A_CORTAR, y), RGB_BLANCO)

            if tipoDeCaptcha == TipoDeCaptcha.AZUL:
                if r < TipoDeCaptcha.AZUL.value[0] and g < TipoDeCaptcha.AZUL.value[1]:
                    imagen_modificada.putpixel((x - ANCHO_A_CORTAR, y), RGB_NEGRO)
                else:
                    imagen_modificada.putpixel((x - ANCHO_A_CORTAR, y), RGB_BLANCO)

            if tipoDeCaptcha == TipoDeCaptcha.CELESTE:
                if r > TipoDeCaptcha.CELESTE.value[0] and g > TipoDeCaptcha.CELESTE.value[1]:
                    imagen_modificada.putpixel((x - ANCHO_A_CORTAR, y), RGB_NEGRO)
                else:
                    imagen_modificada.putpixel((x - ANCHO_A_CORTAR, y), RGB_BLANCO)

    texto = pytesseract.image_to_string(imagen_modificada).upper().replace('\n', '').replace("O", "0").replace("@", "0").replace('-','').replace('—','').replace(' ','').replace('|', '1').replace(')', 'J').replace(']', 'J').replace('}', 'J').replace('{', '1').replace('\\', 'I').replace('¢', 'C').replace('"', 'W').replace('€', '').replace('.', '').replace('¥', 'Y').replace('™', '').replace('?', '7').replace('®', '0').replace('!', 'L')
    print(texto)
    try:
        if contiene_caracteres_especiales(texto):
            # Guardar la imagen solo si el texto contiene caracteres distintos de letras y números
            imagen_modificada.save(f"pruebaFotos/editado_{time.strftime('%Y%m%d%H%M%S', time.localtime())}_{random.randint(1, 1000)}_{texto}.jpg")
    except Exception as ex:
        print(str(ex))
        imagen_modificada.save(f"pruebaFotos/editado_{time.strftime('%Y%m%d%H%M%S', time.localtime())}_{random.randint(1, 1000)}.jpg")
    return texto

# async def human_type(driver, session, element, text):
#         """
#         Types in a way reminiscent of a human, with a random delay in between 50ms to 100ms for every character
#         :param element: Input element to type text to
#         :param text: Input to be typed
#         """
#         for c in text:
#             await asynchronous.send_keys(driver, session, element, c)

#             await asyncio.sleep(random.uniform(0.05, 0.1))
