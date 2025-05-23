import RPi.GPIO as GPIO
import time
from PIL import Image, ImageDraw

# GPIO定义（改成你实际连接的）
DC = 24
RST = 25
CS = 8
CLK = 11
MOSI = 10

# 初始化 GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in [DC, RST, CS, CLK, MOSI]:
    GPIO.setup(pin, GPIO.OUT)

# BitBang SPI 函数
def spi_write(byte):
    for i in range(8):
        GPIO.output(CLK, 0)
        GPIO.output(MOSI, (byte & 0x80) != 0)
        byte <<= 1
        GPIO.output(CLK, 1)

def write_command(cmd):
    GPIO.output(DC, 0)
    GPIO.output(CS, 0)
    spi_write(cmd)
    GPIO.output(CS, 1)

def write_data(data):
    GPIO.output(DC, 1)
    GPIO.output(CS, 0)
    spi_write(data)
    GPIO.output(CS, 1)

def reset():
    GPIO.output(RST, 0)
    time.sleep(0.05)
    GPIO.output(RST, 1)
    time.sleep(0.05)

# 初始化 ST7789（极简版）
def init_lcd():
    reset()
    write_command(0x36); write_data(0x00)
    write_command(0x3A); write_data(0x05)  # 16-bit/pixel
    write_command(0xB2); [write_data(i) for i in (0x0C,0x0C,0x00,0x33,0x33)]
    write_command(0xB7); write_data(0x35)
    write_command(0xBB); write_data(0x19)
    write_command(0xC0); write_data(0x2C)
    write_command(0xC2); write_data(0x01)
    write_command(0xC3); write_data(0x12)
    write_command(0xC4); write_data(0x20)
    write_command(0xC6); write_data(0x0F)
    write_command(0xD0); [write_data(i) for i in (0xA4, 0xA1)]
    write_command(0xE0); [write_data(i) for i in (0xD0,0x04,0x0D,0x11,0x13,0x2B,0x3F,0x54,0x4C,0x18,0x0D,0x0B,0x1F,0x23)]
    write_command(0xE1); [write_data(i) for i in (0xD0,0x04,0x0C,0x11,0x13,0x2C,0x3F,0x44,0x51,0x2F,0x1F,0x1F,0x20,0x23)]
    write_command(0x21) # Display Inversion
    write_command(0x11) # Sleep out
    time.sleep(0.12)
    write_command(0x29) # Display on

# 显示一张图片
def display_image(image):
    # 屏幕分辨率（可调）
    WIDTH, HEIGHT = 240, 240

    # 转换图像为RGB565
    image = image.resize((WIDTH, HEIGHT)).convert('RGB')
    pixelbytes = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b = image.getpixel((x, y))
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            pixelbytes.append((rgb565 >> 8) & 0xFF)
            pixelbytes.append(rgb565 & 0xFF)

    # 写入像素数据
    write_command(0x2A); write_data(0); write_data(0); write_data(0); write_data(WIDTH - 1)
    write_command(0x2B); write_data(0); write_data(0); write_data(0); write_data(HEIGHT - 1)
    write_command(0x2C)
    GPIO.output(DC, 1)
    GPIO.output(CS, 0)
    for byte in pixelbytes:
        spi_write(byte)
    GPIO.output(CS, 1)

# 主程序
if __name__ == "__main__":
    try:
        init_lcd()

        img = Image.new('RGB', (240, 240), 'black')
        draw = ImageDraw.Draw(img)
        draw.rectangle((50, 50, 190, 190), fill='white')
        display_image(img)

        print("图像已显示。LCD已完成。")
    except KeyboardInterrupt:
        GPIO.cleanup()