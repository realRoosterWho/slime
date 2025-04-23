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
    
    def clear(self):
        """清空显示屏"""
        image = Image.new("1" if self.display_type == "OLED" else "RGB", (self.width, self.height))
        self.device.display(image)
        if self.display_type == "OLED":
            self.device.show()
    
    def show_text(self, text, x=10, y=10, font_size=20):
        """显示文本"""
        image = Image.new("1" if self.display_type == "OLED" else "RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        draw.text((x, y), text, font=font, fill=255 if self.display_type == "OLED" else "white")
        self.device.display(image)
        if self.display_type == "OLED":
            self.device.show()
    
    def show_image(self, image_path):
        """显示图片"""
        try:
            img = Image.open(image_path).resize((self.width, self.height))
            self.device.display(img)
            if self.display_type == "OLED":
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
        
        self.device.display(image)
        if self.display_type == "OLED":
            self.device.show()
    
    def draw_menu(self, items, selected_index=0):
        """绘制菜单"""
        image = Image.new("1" if self.display_type == "OLED" else "RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        y = 10
        for i, item in enumerate(items):
            if i == selected_index:
                draw.rectangle((5, y-2, self.width-5, y+12), fill=255 if self.display_type == "OLED" else "white")
                draw.text((10, y), item, font=font, fill=0 if self.display_type == "OLED" else "black")
            else:
                draw.text((10, y), item, font=font, fill=255 if self.display_type == "OLED" else "white")
            y += 15
        
        self.device.display(image)
        if self.display_type == "OLED":
            self.device.show() 