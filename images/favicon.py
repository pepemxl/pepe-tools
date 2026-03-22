from PIL import Image

def crear_favicon(ruta_png, ruta_salida="favicon.ico", tamaños=None):
    """
    Convierte una imagen PNG a favicon.ico con varios tamaños comunes
    """
    if tamaños is None:
        # Tamaños más compatibles en 2025 (incluyendo apple-touch y modernos)
        tamaños = [16, 32, 48, 64, 128, 256]

    # Abrimos la imagen original
    img = Image.open(ruta_png)
    
    # Nos aseguramos que tenga fondo transparente si es necesario
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Lista donde guardaremos las versiones redimensionadas
    iconos = []
    
    for tamaño in tamaños:
        # Redimensionamos manteniendo proporción + recorte si es necesario
        # (mejor calidad que solo resize)
        img_temp = img.copy()
        img_temp.thumbnail((tamaño, tamaño), Image.Resampling.LANCZOS)
        
        # Si no es cuadrada, creamos fondo transparente
        if img_temp.size != (tamaño, tamaño):
            fondo = Image.new("RGBA", (tamaño, tamaño), (0, 0, 0, 0))
            offset = ((tamaño - img_temp.width) // 2, (tamaño - img_temp.height) // 2)
            fondo.paste(img_temp, offset)
            img_temp = fondo
        
        iconos.append(img_temp)

    # Guardamos como .ico (Pillow soporta multi-tamaño)
    iconos[0].save(
        ruta_salida,
        format="ICO",
        append_images=iconos[1:],
        sizes=[(w, w) for w in tamaños],
        quality=100,
        optimize=True
    )
    
    print(f"Favicon creado correctamente → {ruta_salida}")
    print(f"Tamaños incluidos: {tamaños}")


# Ejemplo de uso
if __name__ == "__main__":
    crear_favicon(
        "mi-logo.png",           # ← cambia esta ruta
        "favicon.ico",
        tamaños=[16, 32, 48, 64, 128, 256]   # puedes quitar o agregar
    )