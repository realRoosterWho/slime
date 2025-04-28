from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from PIL import Image, ImageDraw, ImageFont
import time
import board
import busio
from adafruit_ssd1306 import SSD1306_I2C

class DisplayManager:
    def __init__(self, display_type="LCD"):
        self.display_type = display_type
        # 设置默认中文字体路径
        self.font_path = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
        if display_type == "LCD":
            self._init_lcd()
        else:
            self._init_oled()
    
    def _init_lcd(self):
        """初始化LCD显示屏"""
        serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)
        self.device = st7789(serial, width=240, height=240)
        self.width = 240
        self.height = 240
    
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
        image = Image.new("1" if self.display_type == "OLED" else "RGB", (self.width, self.height))
        self._display_image(image)
    
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

    def show_image(self, image_path):
        """显示图片"""
        try:
            img = Image.open(image_path).resize((self.width, self.height))
            if self.display_type == "OLED":
                img = img.convert("1")  # 转换为黑白图像
            self._display_image(img)
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

    def show_text_oled(self, text, font_size=12, chars_per_line=16):
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