FROM public.ecr.aws/lambda/python:3.13

# Instalar dependencias con dnf (Amazon Linux 2023)
RUN dnf install -y tar gzip && \
    dnf install -y \
        alsa-lib \
        atk \
        cups-libs \
        gtk3 \
        ipa-gothic-fonts \
        libXcomposite \
        libXcursor \
        libXdamage \
        libXext \
        libXi \
        libXrandr \
        libXScrnSaver \
        libXtst \
        pango \
        xorg-x11-fonts-100dpi \
        xorg-x11-fonts-75dpi \
        xorg-x11-fonts-cyrillic \
        xorg-x11-fonts-misc \
        xorg-x11-fonts-Type1 \
        xorg-x11-utils && \
    dnf clean all && \
    pip install --upgrade pip

# Instalar dependencias Python
COPY requirements_lambda.txt .
RUN pip install -r requirements_lambda.txt

# Instalar navegador Chromium en una ubicación explícita
RUN PLAYWRIGHT_BROWSERS_PATH=/opt/playwright playwright install chromium

# Definir variable de entorno para que Playwright sepa dónde encontrar el navegador
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# Copiar código fuente
COPY . ${LAMBDA_TASK_ROOT}

# Handler de Lambda
CMD ["lambda_function.lambda_handler"]
