from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from PIL import Image, ImageDraw, ImageFont
import time

serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)
device = st7789(serial, width=240, height=240, h_offset=40, v_offset=53)  # 有些屏幕要加offset

image = Image.new('RGB', device.size, 'black')
draw = ImageDraw.Draw(image)

# 尝试画个白色方块
draw.rectangle((10, 10, 50, 50), fill="white")

# 加载字体
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 24)
    draw.text((20, 100), "你好，世界！", font=font, fill="white")
except Exception as e:
    print(f"字体加载失败: {e}")

# 显示图像
device.display(image)

while True:
    time.sleep(1)