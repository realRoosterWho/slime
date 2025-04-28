# lcd_test.py
from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from PIL import Image, ImageDraw, ImageFont
import time

# 禁用GPIO警告
import RPi.GPIO as GPIO
GPIO.setwarnings(False)

serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)
device = st7789(serial, width=240, height=240)  # 根据你的实际分辨率

# 加载中文字体
font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 24)

# 创建一个纯色背景的测试图像
image = Image.new('RGB', device.size, 'blue')
draw = ImageDraw.Draw(image)

# 在图像上绘制中文
draw.text((10, 10), "你好，世界！", font=font, fill="white")

# 显示图像
device.display(image)

# 保持显示
while True:
    time.sleep(1)
