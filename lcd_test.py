# lcd_test.py
from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from PIL import Image, ImageDraw, ImageFont
import time

serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)
device = st7789(serial, width=240, height=240)  # 根据你的实际分辨率


while True:
    for frame in frames:
        # 加载并调整图片大小
        img = Image.open(frame).resize(device.size)
        
        # 在图片上绘制文字
        draw_temp = ImageDraw.Draw(img)
        draw_temp.text((10, 10), "测试文字", font=font, fill="white")
        
        # 显示图片
        device.display(img)
        time.sleep(0.2)
