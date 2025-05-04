from luma.core.interface.serial import spi
from PIL import Image, ImageDraw, ImageFont
import time
import board
import busio
from adafruit_ssd1306 import SSD1306_I2C
import RPi.GPIO as GPIO

class BitBangLCD:
    def __init__(self):
        # GPIO定义
        self.DC = 24
        self.RST = 25
        self.CS = 8
        self.CLK = 11
        self.MOSI = 10
        self.width = 320   # 横向宽度
        self.height = 240  # 横向高度
        
        # 初始化GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in [self.DC, self.RST, self.CS, self.CLK, self.MOSI]:
            GPIO.setup(pin, GPIO.OUT)
            
        # 初始化LCD
        self._init_lcd()
        
    def _spi_write(self, byte):
        """BitBang SPI写入一个字节"""
        for i in range(8):
            GPIO.output(self.CLK, 0)
            GPIO.output(self.MOSI, (byte & 0x80) != 0)
            byte <<= 1
            GPIO.output(self.CLK, 1)

    def _write_command(self, cmd):
        """写入命令"""
        GPIO.output(self.DC, 0)
        GPIO.output(self.CS, 0)
        self._spi_write(cmd)
        GPIO.output(self.CS, 1)

    def _write_data(self, data):
        """写入数据"""
        GPIO.output(self.DC, 1)
        GPIO.output(self.CS, 0)
        self._spi_write(data)
        GPIO.output(self.CS, 1)

    def _reset(self):
        """重置显示器"""
        GPIO.output(self.RST, 0)
        time.sleep(0.05)
        GPIO.output(self.RST, 1)
        time.sleep(0.05)

    def _init_lcd(self):
        """初始化LCD"""
        self._reset()
        self._write_command(0x36)
        self._write_data(0x00)
        
        # 其他初始化命令
        self._write_command(0x3A); self._write_data(0x05)
        self._write_command(0xB2); [self._write_data(i) for i in (0x0C,0x0C,0x00,0x33,0x33)]
        self._write_command(0xB7); self._write_data(0x35)
        self._write_command(0xBB); self._write_data(0x19)
        self._write_command(0xC0); self._write_data(0x2C)
        self._write_command(0xC2); self._write_data(0x01)
        self._write_command(0xC3); self._write_data(0x12)
        self._write_command(0xC4); self._write_data(0x20)
        self._write_command(0xC6); self._write_data(0x0F)
        self._write_command(0xD0); [self._write_data(i) for i in (0xA4, 0xA1)]
        self._write_command(0xE0); [self._write_data(i) for i in (0xD0,0x04,0x0D,0x11,0x13,0x2B,0x3F,0x54,0x4C,0x18,0x0D,0x0B,0x1F,0x23)]
        self._write_command(0xE1); [self._write_data(i) for i in (0xD0,0x04,0x0C,0x11,0x13,0x2C,0x3F,0x44,0x51,0x2F,0x1F,0x1F,0x20,0x23)]
        self._write_command(0x21)
        self._write_command(0x11)
        time.sleep(0.12)
        self._write_command(0x29)

    def display(self, image):
        """显示图像"""
        # 调整图像大小为屏幕实际大小
        image = image.resize((self.width, self.height)).convert('RGB')
        pixelbytes = []
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = image.getpixel((x, y))
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                pixelbytes.append((rgb565 >> 8) & 0xFF)
                pixelbytes.append(rgb565 & 0xFF)

        # 设置显示区域为全屏
        self._write_command(0x2A)
        [self._write_data(i) for i in (0, 0, (self.width-1) >> 8, (self.width-1) & 0xFF)]
        self._write_command(0x2B)
        [self._write_data(i) for i in (0, 0, (self.height-1) >> 8, (self.height-1) & 0xFF)]
        
        # 写入数据
        self._write_command(0x2C)
        GPIO.output(self.DC, 1)
        GPIO.output(self.CS, 0)
        for byte in pixelbytes:
            self._spi_write(byte)
        GPIO.output(self.CS, 1)

    def clear(self):
        """清空显示"""
        black_image = Image.new('RGB', (self.width, self.height), 'black')
        self.display(black_image)

class DisplayManager:
    def __init__(self, display_type="LCD"):
        self.display_type = display_type
        # 设置默认中文字体路径
        self.font_path = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
        if display_type == "LCD":
            self.device = BitBangLCD()  # 使用新的BitBang实现
            self.width = 240
            self.height = 240
        else:
            self._init_oled()
    
    def _init_oled(self):
        """初始化OLED显示屏"""
        i2c = busio.I2C(board.SCL, board.SDA)
        self.device = SSD1306_I2C(128, 64, i2c, addr=0x3C)
        self.width = 128
        self.height = 64
    
    def _display_image(self, image):
        """统一处理图像显示"""
        if self.display_type == "LCD":
            self.device.display(image)
        else:  # OLED
            self.device.image(image)
            self.device.show()
    
    def clear(self):
        """清空显示屏"""
        if self.display_type == "LCD":
            self.device.clear()  # 使用新的clear方法
        else:  # OLED
            self.device.fill(0)
            self.device.show()
    
    def show_text(self, text, x=10, y=10, font_size=20, max_width=None):
        """显示文本，支持中文和自动换行"""
        image = Image.new("1" if self.display_type == "OLED" else "RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        # 尝试加载中文字体，如果失败则使用默认字体
        try:
            font = ImageFont.truetype(self.font_path, font_size)
        except:
            print("警告：无法加载中文字体，将使用默认字体")
            font = ImageFont.load_default()

        if max_width:
            self._draw_wrapped_text(draw, text, x, y, max_width, font)
        else:
            # 处理手动换行（\n）
            lines = text.split('\n')
            y_text = y
            for line in lines:
                draw.text((x, y_text), line, font=font, 
                         fill=255 if self.display_type == "OLED" else "white")
                y_text += font.getsize(line)[1] + 5  # 行间距为5像素

        self._display_image(image)

    def _draw_wrapped_text(self, draw, text, x, y, max_width, font):
        """绘制自动换行的文本"""
        # 计算每行大约能容纳多少个字符
        avg_char_width = font.getlength("测")/2  # 获取一个汉字的平均宽度
        chars_per_line = int(max_width / avg_char_width)
        
        # 使用textwrap进行自动换行
        import textwrap
        lines = textwrap.wrap(text, width=chars_per_line)
        
        # 绘制每一行
        y_text = y
        for line in lines:
            draw.text((x, y_text), line, font=font, 
                     fill=255 if self.display_type == "OLED" else "white")
            y_text += font.getsize(line)[1] + 5  # 行间距为5像素

    def show_image(self, image_input):
        """显示图片
        Args:
            image_input: 可以是图片文件路径(str)或PIL Image对象
        """
        try:
            # 如果输入是字符串（文件路径），则打开图片
            if isinstance(image_input, str):
                img = Image.open(image_input)
            # 如果输入已经是PIL Image对象，直接使用
            elif isinstance(image_input, Image.Image):
                img = image_input
            else:
                raise ValueError("输入必须是图片路径或PIL Image对象")

            if self.display_type == "LCD":
                self.device.display(img)
            else:  # OLED
                img = img.convert("1")  # 转换为黑白图像
                self.device.image(img)
                self.device.show()
        except Exception as e:
            print(f"显示图片时出错: {e}")
    
    def show_animation(self, image_paths, delay=0.2):
        """显示动画"""
        try:
            while True:
                for path in image_paths:
                    self.show_image(path)
                    time.sleep(delay)
        except KeyboardInterrupt:
            self.clear()
    
    def draw_progress_bar(self, progress, x=10, y=30, width=100, height=10):
        """绘制进度条"""
        image = Image.new("1" if self.display_type == "OLED" else "RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        # 绘制背景
        draw.rectangle((x, y, x + width, y + height), outline=255 if self.display_type == "OLED" else "white")
        
        # 绘制进度
        progress_width = int(width * progress)
        draw.rectangle((x, y, x + progress_width, y + height), fill=255 if self.display_type == "OLED" else "white")
        
        self._display_image(image)
    
    def draw_menu(self, items, selected_index=0):
        """绘制菜单，支持中文"""
        image = Image.new("1" if self.display_type == "OLED" else "RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype(self.font_path, 12)
        except:
            print("警告：无法加载中文字体，将使用默认字体")
            font = ImageFont.load_default()
        
        y = 10
        for i, item in enumerate(items):
            if i == selected_index:
                draw.rectangle((5, y-2, self.width-5, y+12), 
                             fill=255 if self.display_type == "OLED" else "white")
                draw.text((10, y), item, font=font, 
                         fill=0 if self.display_type == "OLED" else "black")
            else:
                draw.text((10, y), item, font=font, 
                         fill=255 if self.display_type == "OLED" else "white")
            y += 15
        
        self._display_image(image)

    def show_text_oled(self, text, font_size=12, chars_per_line=9):
        """专门为OLED优化的文本显示
        Args:
            text: 要显示的文本
            font_size: 字体大小，默认12
            chars_per_line: 每行字符数，默认8
        """
        # 创建新图像
        image = Image.new("1", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype(self.font_path, font_size)
        except:
            print("警告：无法加载中文字体，将使用默认字体")
            font = ImageFont.load_default()

        # 如果文本中已经有换行符，就使用现有的换行
        # 如果没有换行符，则按指定字符数添加换行
        if '\n' not in text:
            lines = []
            for i in range(0, len(text), chars_per_line):
                lines.append(text[i:i + chars_per_line])
            text = '\n'.join(lines)
        
        # 处理换行
        lines = text.split('\n')
        y = 10  # 起始y坐标
        
        # 绘制每一行
        for line in lines:
            draw.text((10, y), line, font=font, fill=255)
            y += 20  # 固定行间距为20像素

        self._display_image(image) 