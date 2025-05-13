import asyncio
import traceback
from selenium.webdriver.common.by import By
from captchaCaqui.solver2 import RecaptchaSolver
import captchaCaqui.asynchronous as asynchronous

async def obtenerIframeDeCaptcha(driver_url, session, idElementoABuscar):
    boton_captcha_audio = None
    iframes = await asynchronous.find_elements(driver_url, session, By.TAG_NAME, 'iframe')

    for recaptcha_iframe in iframes:
        try:
            # Cambia al contexto del iframe
            await asynchronous.switch_to_frame(driver_url, session, recaptcha_iframe)

            # Verifica si el div está presente dentro del iframe
            boton_captcha_audio = await asynchronous.find_element(driver_url, session, By.ID, idElementoABuscar)

            # Realiza acciones con el div
            # Por ejemplo, puedes imprimir su texto
            await asynchronous.switch_to_default_content(driver_url, session)
            # Sal del bucle si el div es encontrado
            if type(boton_captcha_audio) == str and 'no such element' in boton_captcha_audio:
                continue
            else:
                break
        except:
            await asynchronous.switch_to_default_content(driver_url, session)
            # Si el div no está presente en el iframe actual, pasa al siguiente iframe
            continue
    
    if boton_captcha_audio == None:
        return None
    return recaptcha_iframe

async def resolverCaptcha(driver_url, session):
    try:

        # Primero apreto el boton para hacer el recaptcha que se encuentra en un frame.
        recaptcha_iframe = await obtenerIframeDeCaptcha(driver_url, session, 'rc-anchor-container')
        if recaptcha_iframe == None:
            raise Exception('No se encontró el iframe del captcha. Puede ser que no haya captcha para resolver.')
        await asynchronous.switch_to_frame(driver_url, session, recaptcha_iframe)
        try:
            botonRecaptcha = await asynchronous.find_element(driver_url, session, By.ID, 'rc-anchor-container')
            if botonRecaptcha:
                await asynchronous.click(driver_url, session, botonRecaptcha)
        except Exception:
            ...
        await asynchronous.switch_to_default_content(driver_url, session)

        # Ahora voy al frame donde esta el audio y hago toda la logica de hacer el captcha.        
        recaptcha_iframe = await obtenerIframeDeCaptcha(driver_url, session, 'recaptcha-audio-button')
        if recaptcha_iframe == None:
            raise Exception('No se encontró el iframe del captcha. Puede ser que no haya captcha para resolver.')
        await asyncio.sleep(3) # Espero unos segundos a que termine de cambiar de frame.
        await asynchronous.switch_to_frame(driver_url, session, recaptcha_iframe)
        solver = RecaptchaSolver(driver=None, driver_url=driver_url, session=session)
        await solver.solve_recaptcha_v2_challenge(iframe=recaptcha_iframe)
        await asynchronous.switch_to_default_content(driver_url, session)
    except Exception:
        traceback.print_exc()
        return Exception('No se pudo resolver el captcha.')