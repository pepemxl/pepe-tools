# pepe-tools
Set of utils for development

## Instalación y Uso (Docker)

El proyecto incluye un entorno preconfigurado basado en Docker con Ubuntu 24.04 y Python 3.13. Esto te permite ejecutar las herramientas CLI (`pepe-tools`) y mantener sincronizado tu código, sin ensuciar tu entorno local.

### Prerrequisitos
- [Docker](https://docs.docker.com/get-docker/) instalado.
- Opcionalmente `make` instalado en tu sistema si usarás los atajos.

### Paso 1: Construir la imagen de Docker
Construye el contenedor ejecutando:
```bash
make build
# Sin Make: docker build -t pepe-tools-env .
```

### Paso 2: Ejecutar el entorno virtualizado
Entra a la consola interactiva del contenedor:
```bash
make shell
```
*Si no usas `make`, puedes correr este equivalente en PowerShell:*
```powershell
docker run -it --rm -v "${PWD}:/app" pepe-tools-env bash
```

Una vez dentro, tu CLI `pepe-tools` ya estará instalada localmente en modo desarrollo (`pip install -e .`). 

## Herramientas de Desarrollo

El `Makefile` ofrece atajos útiles para tareas comunes (puedes correrlos dentro del contenedor interactivo de Ubuntu o en tu máquina local si tienes instaladas las herramientas):

- `make test`: Ejecuta pruebas unitarias (`pytest`).
- `make format`: Da formato automático al código con `black`.
- `make lint`: Verifica el estilo del código usando `flake8`.
- `make clean`: Elimina de manera recursiva la caché (`__pycache__`), métricas de *coverage* y archivos de `build`.
