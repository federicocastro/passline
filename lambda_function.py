import json
from obtener_filas_sync_playwright_lambda import ejecutar_navegador_sync
from uuid import uuid4

def lambda_handler(event, context):
    task_id = uuid4().hex
    fila_id = ejecutar_navegador_sync(task_id)

    return {
        'statusCode': 200,
        'body': json.dumps({'task_id': task_id, 'fila_id': fila_id})
    }
