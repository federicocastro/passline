from PIL import Image, ImageFilter
import pytesseract
import os
from enum import Enum

CARPETA = 'captchas'
ANCHO_A_CORTAR = 50
RGB_NEGRO = (0, 0, 0)
RGB_BLANCO = (255, 255, 255)
CUADRICULA_GRIS = ()

class TipoDeCaptcha(Enum):
    CUADRICULADO = (235, 235, 235)  # Los RGB son iguales a estos valores
    CELESTE = (130, 130, 180)  # Los RGB son mayores a estos valores
    AZUL = (100, 100, 130)  # Los RGB son menores a estos valores


def eliminar_fondo(i, ruta_imagen):
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
            

    texto = pytesseract.image_to_string(imagen_modificada)
    print(texto)

    imagen_modificada.save(f"captcha_modificado_{i}.png")

archivos = os.listdir(CARPETA)

# Iterar sobre cada archivo
for i, archivo in enumerate(archivos):
    # Obtener la ruta completa del archivo
    ruta_archivo = os.path.join(CARPETA, archivo)
    if 'cuadriculado' in ruta_archivo:
        eliminar_fondo(i, ruta_archivo)

# eliminar_fondo('azul.jpeg', 'captchas/azul.jpeg')
# eliminar_fondo('captcha_modificado_azul.jpeg', 'captcha_modificado_azul.jpeg')