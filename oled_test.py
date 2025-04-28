import board
import busio
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw, ImageFont

# 初始化I2C
i2c = busio.I2C(board.SCL, board.SDA)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# 创建图像
image = Image.new("1", (128, 64))
draw = ImageDraw.Draw(image)

# 加载中文字体文件（需要先准备字体文件）
# 请确保将字体文件放在正确的路径下
font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 12)

# 使用中文字体绘制文本
draw.text((10, 10), "你好，世界！", font=font, fill=255)

# 显示图像
oled.image(image)
oled.show()
