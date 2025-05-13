
import os
import time

FILAS_POR_ARCHIVO = 10
PREFIJO_NOMBRE_ARCHIVO = "filas"
CARPETA_ORIGEN = "filasObtenidas"
CARPETA_DESTINO = "filasAValidar"


def reorganizarFilas(carpeta_origen, carpeta_destino, filas_por_archivo):
    archivos_origen = os.listdir(carpeta_origen)
    filas_totales = []

    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # Leer todas las filas de los archivos de origen
    for archivo in archivos_origen:
        ruta_archivo_origen = os.path.join(carpeta_origen, archivo)
        if not os.path.isfile(ruta_archivo_origen):
            continue

        with open(ruta_archivo_origen, 'r') as archivo_origen:
            filas = archivo_origen.readlines()
            filas_totales.extend(filas)

    # Dividir las filas en archivos más pequeños
    num_archivos = (len(filas_totales) - 1) // filas_por_archivo + 1
    inicio = 0
    print(f'Hay un total de {len(filas_totales)} de filas que se dividirán en {num_archivos} archivos.')

    for i in range(num_archivos):
        fin = inicio + filas_por_archivo
        subfilas = filas_totales[inicio:fin]

        indice = i + 1
        if indice == 1:
            indice = ''

        archivo_destino = f"{PREFIJO_NOMBRE_ARCHIVO}{indice}.txt"
        ruta_archivo_destino = os.path.join(carpeta_destino, archivo_destino)

        if os.path.exists(ruta_archivo_destino):
            timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
            archivo_destino = f"{PREFIJO_NOMBRE_ARCHIVO}{indice}_{timestamp}.txt"
            ruta_archivo_destino = os.path.join(carpeta_destino, archivo_destino)

        with open(ruta_archivo_destino, 'w') as archivo_destino:
            archivo_destino.writelines(subfilas)

        inicio = fin

    for archivo in archivos_origen:
        ruta_archivo_origen = os.path.join(carpeta_origen, archivo)
        os.remove(ruta_archivo_origen)

if __name__ == "__main__":
    start = time.time()
    reorganizarFilas(CARPETA_ORIGEN, CARPETA_DESTINO, FILAS_POR_ARCHIVO)
    end = time.time()
    print(f"TIEMPO QUE TARDO: {end-start:.4f} sec")