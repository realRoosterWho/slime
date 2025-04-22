# lcd_test.py
from luma.core.interface.serial import spi
from luma.lcd.device import st7735  # 或 st7789 看你实际用的
from PIL import Image
import time

serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)
device = st7735(serial, width=128, height=160)

frames = ["slime1.png", "slime2.png", "slime3.png"]  # 替换为你准备的动图帧

while True:
    for frame in frames:
        img = Image.open(frame).resize(device.size)
        device.display(img)
        time.sleep(0.2)
