import boto3
import json
import sys
import uuid

# Configuración
FUNCTION_NAME = "lambda_captcha"  # reemplaza por el nombre exacto de tu Lambda
REGION_NAME = "us-east-1"

# Número de invocaciones pasado por línea de comandos
num_invocations = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# Crear cliente Lambda
lambda_client = boto3.client('lambda', region_name=REGION_NAME)

for i in range(num_invocations):
    payload = {
        "task_id": str(uuid.uuid4())
    }

    response = lambda_client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType='Event',  # Asíncrono
        Payload=json.dumps(payload)
    )

    print(f"Invocación {i+1}/{num_invocations} enviada, status: {response['StatusCode']}")
