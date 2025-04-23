from luma.core.interface.serial import i2c
from luma.oled.device import ssd1315
from luma.core.render import canvas
from PIL import ImageFont

serial = i2c(port=1, address=0x3C)
device = ssd1315(serial, width=128, height=64)

with canvas(device) as draw:
    draw.text((10, 10), "Hello Slime!", fill="white")

print("Displaying image...")