from luma.core.interface.serial import bitbang
from luma.lcd.device import st7789
from PIL import Image, ImageDraw, ImageFont
import time

# 使用 bit-banged SPI
serial = bitbang(
    gpio_DC=24,    # Data/Command
    gpio_RST=25,   # Reset
    gpio_CS=8,     # Chip Select
    gpio_MOSI=10,  # Master Out Slave In (数据线)
    gpio_CLK=11    # Clock (时钟线)
)

# 初始化 ST7789 显示设备
device = st7789(serial, width=240, height=240)

# 创建新图像
image = Image.new('RGB', device.size, 'black')
draw = ImageDraw.Draw(image)

# 画个白色方块
draw.rectangle((10, 10, 50, 50), fill="white")

# 加载中文字体
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 24)
    draw.text((20, 100), "你好，世界！", font=font, fill="white")
except Exception as e:
    print(f"字体加载失败: {e}")

# 显示图像
device.display(image)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n程序被用户中断")
    # 清屏
    device.clear()