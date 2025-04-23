# oled_test.py
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw

# 初始化 I2C 和设备
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

# 创建画布并绘图
img = Image.new("1", device.size)
draw = ImageDraw.Draw(img)
draw.rectangle(device.bounding_box, outline=255, fill=0)
draw.text((10, 10), "Hello Slime!", fill=255)

# 发送到显示屏
device.display(img)
