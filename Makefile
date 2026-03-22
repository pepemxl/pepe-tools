.PHONY: build shell test lint format clean

IMAGE_NAME = pepe-tools-env

# Construye la imagen de Docker
build:
	docker build -t $(IMAGE_NAME) .

# Ejecuta el contenedor de forma interactiva montando el código en tiempo real
shell:
	docker run -it --rm -v "$(CURDIR):/app" $(IMAGE_NAME) bash

# Ejecuta las pruebas usando pytest (debe estar en dev dependencies)
test:
	pytest tests/

# Revisa el código buscando errores de estilo con flake8
lint:
	flake8 src/ tests/

# Formatea el código automáticamente usando black
format:
	black src/ tests/

# Limpia los archivos de caché y compilados locales
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage *.egg-info build/ dist/ .venv/
