import asyncio
import time

import aiohttp

from obtenerFilas import CODIGO_ARTISTA, EMPRESA_TICKETS, guardarIdFilas


async def obtenerLambda(session, url):
    params = {
        "empresaTickets": EMPRESA_TICKETS,
        "codigoArtista": CODIGO_ARTISTA
    }

    async with session.get(url, params=params) as response:
        data = await response.text()
        print("Respuesta:", data, type(data))
        if not data:
            print('reconstruir')
            params['reconstruir'] = 'true'
            async with session.get(url, params=params) as response:
                data = await response.text()
        return data

async def llamarMetodosAsync(metodosALlamarAsync):
    return await asyncio.gather(*metodosALlamarAsync)

async def obtenerLambdasAsync():
    urls = ['https://wtsdhu7qf6zuzbqinrrz7x4fqm0jfony.lambda-url.us-east-2.on.aws/',
        'https://ngeztsqr236t2gxavm5yr5wrdi0yrvzv.lambda-url.us-east-2.on.aws/',
        'https://kte4dpmenhcpysbwiqonge2yum0namld.lambda-url.us-east-2.on.aws/'
        ] 
    llamadasAHacerAsync = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            llamadasAHacerAsync.append(
                obtenerLambda(session, url)
            )
        respuestasLlamadas = await llamarMetodosAsync(llamadasAHacerAsync)
    return respuestasLlamadas

if __name__ == "__main__":
    for i in range(0, 1):
        start = time.time()
        responses = asyncio.run(obtenerLambdasAsync())
        guardarIdFilas(responses)
        end = time.time()
        print(f"TIEMPO QUE TARDO ATR: {end-start:.2f} sec")