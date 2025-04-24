# lcd_test.py
from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from PIL import Image
import time

serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)
device = st7789(serial, width=240, height=240)  # 根据你的实际分辨率

frames = ["slime1.png", "slime2.png", "slime3.png"]  # 替换为你准备的动图帧
# 这次用test_1.jpg到test_10.jpg
frames = [f"test_{i+1}.jpg" for i in range(10)]

while True:
    for frame in frames:
        img = Image.open(frame).resize(device.size)
        device.display(img)
        time.sleep(0.2)
