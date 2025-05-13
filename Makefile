# Makefile para ejecutar obtener_filas_sync.py en paralelo
export AWS_PROFILE=fedexcastro

NUM_TASKS=5
SCRIPT=obtener_filas_sync.py
# Configuración inicial (personaliza esto)
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=798576948313
IMAGE_NAME=lambda-captcha
ECR_REPO=$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(IMAGE_NAME)

# Comando para autenticarse en AWS ECR
.PHONY: login
login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

# Comando para construir la imagen Docker
.PHONY: build
build:
	docker buildx build --platform linux/amd64 -t $(IMAGE_NAME) .

# Etiquetar la imagen para subirla a AWS ECR
.PHONY: tag
tag:
	docker tag $(IMAGE_NAME):latest $(ECR_REPO):latest

# Subir la imagen Docker etiquetada a AWS ECR
.PHONY: push
push: login
	docker push $(ECR_REPO):latest

# Hacer build + tag + push en un solo paso
.PHONY: deploy
deploy: build tag push
	echo "Imagen construida, etiquetada y subida exitosamente a AWS ECR."

# Ejecutar múltiples tareas locales en paralelo
.PHONY: run-parallel
run-parallel:
	seq 0 49 | xargs -P 50 -I{} python obtener_filas_sync.py {}

# Limpieza de imágenes Docker no usadas (opcional pero recomendado)
.PHONY: clean-docker
clean-docker:
	docker system prune -f


NUM_INVOCATIONS=10
invoke-lambda:
	@echo "Invocando Lambda ${NUM_INVOCATIONS} veces..."
	python invoke_lambda.py ${NUM_INVOCATIONS}
