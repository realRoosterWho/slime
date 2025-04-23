from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=64)

# 设置对比度最大
device.contrast(255)

# 创建一个全白的图像
img = Image.new("1", (128, 64), color=1)
device.display(img)

print("试图强制点亮整个屏幕")
