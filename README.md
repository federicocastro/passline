# Tickets Conciertos

Primero tenes que descargar chromedriver desde acá: https://chromedriver.chromium.org/downloads
Version Beta de chrome driver: https://googlechromelabs.github.io/chrome-for-testing/#stable

Una vez descargado guarda el archivo.

Seguir pasos de instalación: https://github.com/thicccat688/selenium-recaptcha-solver
Pasar el codigo de asynchronous.py a caqui

Comando para correr el servidor de Chrome: ./chromedriver --port=9999

Comandos a realizar:

Paso 1: py .\obtenerFilas.py
- Se farmean numeros de filas (recomendable de a 20).
- Los numeros de filas obtenidos se guardaran en archivos dentro de la carpeta filasObtenidas. 

Paso 2: py .\reorganizarFilas.py
- Se reorganizadas las filas obtenidas en archivos de cantidad fija de filas (recomendable 60).
- Las filas reorganizadas se guardarán en archivos dentro de la carpeta filasAValidar.

Paso 3: py .\validarPosicionFila.py
- Se valida la posición de las filas (recomendable de a 5-15 al mismo tiempo dependiendo la computadora)
Se generarán tres archivos:
- filasValidadas: en esta carpeta se van a guardar las filas que superen un valor mínimo (es decir, están dentro de todo cerca de llegar al turno).
- filasValorNoAlcanzado: en esta carpeta se van a guardar filas que se pudieron validar pero dicho valor no llego a mínimo deseado.
- validacionesFallidas: en esta carpeta se van a guardar filas que no se pudieron validar (ya sea porque el turno expiró o por error de captcha)