from PIL import Image, ImageDraw
import os

# Crear un icono simple
size = (256, 256)
image = Image.new('RGBA', size, (0, 128, 255))  # Color azul
draw = ImageDraw.Draw(image)

# Dibujar un símbolo de servicio
draw.rectangle([50, 50, 206, 206], fill=(255, 255, 255, 200), outline=(0, 0, 0, 255))
draw.text((80, 100), "SA", fill=(0, 0, 0), font=None)

# Guardar como ICO
image.save('icon.ico', format='ICO')
