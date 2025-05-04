import board
import busio
from PIL import Image, ImageDraw, ImageFont
from adafruit_ssd1306 import SSD1306_I2C

def test_oled():
    # 初始化I2C
    i2c = busio.I2C(board.SCL, board.SDA)
    
    # 初始化OLED (128x64)
    oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)
    
    # 创建空白图像
    image = Image.new('1', (128, 64))
    draw = ImageDraw.Draw(image)
    
    try:
        # 尝试加载中文字体
        font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 12)
    except:
        print("无法加载中文字体，使用默认字体")
        font = ImageFont.load_default()
    
    # 绘制测试文本
    draw.text((0, 0), "OLED测试", font=font, fill=255)
    draw.text((0, 20), "I2C接口", font=font, fill=255)
    draw.text((0, 40), "SDA: GPIO 2", font=font, fill=255)
    draw.text((0, 50), "SCL: GPIO 3", font=font, fill=255)
    
    # 显示图像
    oled.image(image)
    oled.show()

if __name__ == "__main__":
    try:
        test_oled()
        print("OLED测试运行中... 按Ctrl+C退出")
        while True:
            pass
    except KeyboardInterrupt:
        print("\n程序已退出")
