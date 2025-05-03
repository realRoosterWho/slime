from luma.core.interface.serial import bitbang
from luma.lcd.device import st7789
from PIL import Image, ImageDraw, ImageFont
import time
import signal
import sys
import RPi.GPIO as GPIO

def cleanup_handler(signum, frame):
    """清理资源并优雅退出"""
    print("\n🛑 检测到中断信号，正在清理资源...")
    try:
        device.clear()
        GPIO.cleanup()
        print("✅ 已清理显示资源")
    except:
        pass
    sys.exit(0)

# 设置信号处理
signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)

try:
    # GPIO 引脚定义
    DC_PIN = 24    # Data/Command
    RST_PIN = 25   # Reset
    CS_PIN = 8     # Chip Select
    MOSI_PIN = 10  # Master Out Slave In (数据线)
    CLK_PIN = 11   # Clock (时钟线)

    # 初始化 GPIO
    GPIO.setmode(GPIO.BCM)  # 使用 BCM 编号方式
    GPIO.setwarnings(False)
    
    # 设置所有用到的引脚
    for pin in [DC_PIN, RST_PIN, CS_PIN, MOSI_PIN, CLK_PIN]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    print("初始化显示设备...")
    # 使用 bitbang
    serial = bitbang(
        gpio_DC=DC_PIN,
        gpio_RST=RST_PIN,
        gpio_CS=CS_PIN,
        gpio_MOSI=MOSI_PIN,
        gpio_CLK=CLK_PIN,
        gpio_mode=GPIO.BCM
    )

    device = st7789(serial, width=240, height=240, h_offset=40, v_offset=53)
    
    print("创建测试图像...")
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
    print("显示图像...")
    device.display(image)

    print("运行中... (按 Ctrl+C 退出)")
    while True:
        time.sleep(1)

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    GPIO.cleanup()

except KeyboardInterrupt:
    print("\n程序被用户中断")
    device.clear()
    GPIO.cleanup()