FROM ubuntu:24.04

# Evitar prompts interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Actualizar repositorios e instalar dependencias básicas
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    build-essential \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.13 \
    python3.13-venv \
    python3.13-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear un entorno virtual usando Python 3.13 y activarlo
ENV VIRTUAL_ENV=/opt/venv
RUN python3.13 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Actualizar herramientas de empaquetado
RUN pip install --upgrade pip setuptools wheel

# Establecer nuestro directorio de trabajo
WORKDIR /app

# Copiar el código del proyecto
COPY . /app/

# Instalar finalmente en modo editable e instalar dependencias (dev opcional)
RUN pip install -e .[dev]

# Dejar una terminal por defecto al arrancar el contenedor
CMD ["bash"]
