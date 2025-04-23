# oled_test.py
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import ImageDraw, ImageFont, Image

serial = i2c(port=1, address=0x3C)  # 注意 address（可能是 0x3C 或 0x3D）
device = ssd1306(serial)

img = Image.new("1", device.size)
draw = ImageDraw.Draw(img)

draw.text((0, 0), "Slime Device", fill=255)
draw.text((0, 20), "Battery: 87%", fill=255)
device.display(img)