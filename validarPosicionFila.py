from datetime import datetime
import os
import traceback
import time
import asyncio
import asyncio
import time
from caqui import asynchronous
from obtenerFilas import URL

NOMBRE_ARCHIVO = 'filas.txt'
MAX_CONCURRENCY = 60  # number of webdriver instances running
sem = asyncio.Semaphore(MAX_CONCURRENCY)
ESPERA_CARGA_PAGINA = 8 # Tiempo de sleep que tiene selenium una vez cargada la pagina para empezar a obtener datos.
VALOR_POSICION_ACEPTABLE_FILA = 30 # Es un numero de 0 a 100 en porcentaje el cual indica la ubicación en fila.
UBICACION_FILAS_A_VALIDAR = 'filasAValidar'


async def obtenerPosicionFila(idFila):
    async with sem:
        try:
            driver_url = "http://127.0.0.1:9999"
            capabilities = {
                "desiredCapabilities": {
                    "browserName": "chrome",
                    "marionette": True,
                    "acceptInsecureCerts": True,
                    "pageLoadStrategy": "normal",
                    #"goog:chromeOptions": {"extensions": [], "args": ["--headless"]},
                    #--headless hace que no te abra pestañas de chrome, pero suelen pensar que sos bot cuando lo haces.
                }
            }
            
            # Abro sesión
            session = await asynchronous.get_session(driver_url, capabilities)
            valorProgressBar = None
            try:
                await asynchronous.go_to_page(
                    driver_url,
                    session,
                    f'{URL}&q={idFila}',
                )

                await asyncio.sleep(ESPERA_CARGA_PAGINA)

                valorProgressBar = await obtenerValorProgressBar(driver_url, session)
            
            except Exception:
                traceback.print_exc()

            await asynchronous.close_session(driver_url, session)
            print("Valor Progress Bar", valorProgressBar, idFila)
            return valorProgressBar, idFila
        except Exception:
            return None, idFila

async def llamarMetodosAsync(metodosALlamarAsync):
    return await asyncio.gather(*metodosALlamarAsync)

async def obtenerValorProgressBar(driver_url, session):
    locator = f"//div[@id='MainPart_divProgressbar']"
    anchors = await asynchronous.find_elements(driver_url, session, 'xpath', locator)

    if anchors:
        return int(await asynchronous.get_attribute(driver_url, session, anchors[0], "aria-valuenow") or 0)

    return None

def guardarFilasValidadas(respuestas):
    datosProcesados = []
    datosValorNoAceptable = []
    datosFallidos = []
    for valor, filaId in respuestas:
        if valor is None:
            datosFallidos.append(filaId)
        else:
            if valor >= VALOR_POSICION_ACEPTABLE_FILA:
                datosProcesados.append((valor, filaId))
            else:
                datosValorNoAceptable.append(filaId)

    datosProcesadosOrdenados = sorted(datosProcesados, key=lambda x: x[0], reverse=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    carpeta = 'filasValidadas'
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    
    if datosProcesadosOrdenados:
        rutaArchivoValidado = os.path.join(carpeta, f'filas-{timestamp}.txt')
        with open(rutaArchivoValidado, 'w') as f:
            for fila in datosProcesadosOrdenados:
                f.write(f"{fila[0]};{URL}&q={fila[1]}\n")

    carpeta = 'validacionesFallidas'
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    if datosFallidos:
        rutaArchivoFallido = os.path.join(carpeta, f'filas-{timestamp}.txt')
        with open(rutaArchivoFallido, 'w') as f:
            for fila in datosFallidos:
                f.write(f"{fila}\n")

    carpeta = 'filasValorNoAlcanzado'
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    if datosValorNoAceptable:
        rutaArchivoFallido = os.path.join(carpeta, f'filas-{timestamp}.txt')
        with open(rutaArchivoFallido, 'w') as f:
            for fila in datosValorNoAceptable:
                f.write(f"{fila}\n")

def borrarArchivoValidadoYPrepararSiguiente():
    archivoValidado = os.path.join(UBICACION_FILAS_A_VALIDAR, NOMBRE_ARCHIVO)
    os.remove(archivoValidado)
    archivos = os.listdir(UBICACION_FILAS_A_VALIDAR)

    if archivos:
        # Seleccionar el primer archivo de la lista
        nombre_archivo = archivos[0]
        
        # Obtener la ruta completa del archivo original
        ruta_archivo_origen = os.path.join(UBICACION_FILAS_A_VALIDAR, nombre_archivo)

        # Obtener la ruta completa del archivo con el nuevo nombre
        ruta_nuevo_archivo = os.path.join(UBICACION_FILAS_A_VALIDAR, NOMBRE_ARCHIVO)

        # Cambiar el nombre del archivo
        os.rename(ruta_archivo_origen, ruta_nuevo_archivo)

if __name__ == "__main__":
    start = time.time()

    llamadasAHacerAsync = []
    with open(f'{UBICACION_FILAS_A_VALIDAR}/{NOMBRE_ARCHIVO}', 'r') as file:
        for line in file:
            print("LINEA", line.strip())
            llamadasAHacerAsync.append(
                obtenerPosicionFila(line.strip())
            )
    respuestas = asyncio.run(llamarMetodosAsync(llamadasAHacerAsync))

    print(respuestas)
    guardarFilasValidadas(respuestas)
    borrarArchivoValidadoYPrepararSiguiente()
    end = time.time()
    print(f"TIEMPO QUE TARDO: {end-start:.2f} sec")