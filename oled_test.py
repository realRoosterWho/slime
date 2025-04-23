import board
import busio
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw

# 初始化I2C
i2c = busio.I2C(board.SCL, board.SDA)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# 创建图像
image = Image.new("1", (128, 64))
draw = ImageDraw.Draw(image)
draw.text((10, 10), "( ；´Д｀)i just wanna die...qwq", fill=255)

# 显示图像
oled.image(image)
oled.show()
