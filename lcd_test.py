from luma.core.interface.serial import bitbang
from luma.lcd.device import st7789
from PIL import Image, ImageDraw, ImageFont
import time
import signal
import sys

def cleanup_handler(signum, frame):
    """清理资源并优雅退出"""
    print("\n🛑 检测到中断信号，正在清理资源...")
    try:
        device.clear()
        print("✅ 已清理显示资源")
    except:
        pass
    sys.exit(0)

# 设置信号处理
signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)

# 使用 bitbang 代替 SPI
serial = bitbang(
    gpio_DC=24,    # Data/Command
    gpio_RST=25,   # Reset
    gpio_CS=8,     # Chip Select
    gpio_MOSI=10,  # Master Out Slave In (数据线)
    gpio_CLK=11    # Clock (时钟线)
)

device = st7789(serial, width=240, height=240, h_offset=40, v_offset=53)

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

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n程序被用户中断")
    device.clear()