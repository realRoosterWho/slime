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
        self._write_data(0xF0)
        
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
        # 初始化 GPIO 模式
        if not GPIO.getmode():  # 如果 GPIO 模式还没有被设置
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
        self.display_type = display_type
        # 设置默认中文字体路径
        self.font_path = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
        if display_type == "LCD":
            self.device = BitBangLCD()  # 使用新的BitBang实现
            self.width = 320  # 修正为实际的LCD尺寸
            self.height = 240
        else:  # OLED
            self._init_oled()
        self.current_menu_index = 0  # 当前菜单选择索引
        self.indicator_frame = 0     # 指示器动画帧
        self.last_indicator_update = time.time()
        self.indicator_interval = 0.5  # 指示器更新间隔（秒）
    
    def _init_oled(self):
        """初始化OLED显示屏"""
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)
        self.width = 128
        self.height = 64
        # 为OLED创建绘图对象
        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
    
    def _display_image(self, image):
        """统一处理图像显示"""
        if self.display_type == "LCD":
            # 只有LCD需要旋转180度
            rotated_image = image.rotate(180)
            self.device.display(rotated_image)
        else:  # OLED保持原样
            self.oled.image(image)
            self.oled.show()
    
    def clear(self):
        """清空显示屏"""
        if self.display_type == "LCD":
            self.device.clear()  # 使用新的clear方法
        else:  # OLED
            self.oled.fill(0)
            self.oled.show()
    
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
            for i, line in enumerate(lines):
                draw.text((x, y + i * font_size * 1.2), line, font=font, fill="white" if self.display_type == "OLED" else "white")
        
        self._display_image(image)
    
    def _draw_wrapped_text(self, draw, text, x, y, max_width, font):
        """绘制自动换行的文本"""
        words = text.split(' ')
        lines = []
        current_line = words[0]
        
        for word in words[1:]:
            # 检查当前行加上新单词的宽度是否超过最大宽度
            test_line = current_line + " " + word
            text_width = draw.textlength(test_line, font=font)
            
            if text_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)
        
        # 绘制所有行
        for i, line in enumerate(lines):
            draw.text((x, y + i * font.getsize('A')[1] * 1.2), line, font=font, fill="white" if self.display_type == "OLED" else "white")

    def show_image(self, image):
        """显示图像"""
        # 调整图像大小为显示设备的尺寸
        resized_image = image.resize((self.width, self.height))
        
        # 根据显示类型进行转换
        if self.display_type == "OLED":
            # 转换为1位图像（仅黑白）
            bw_image = resized_image.convert("1")
            self._display_image(bw_image)
        else:  # LCD
            # LCD可以显示彩色
            rgb_image = resized_image.convert("RGB")
            self._display_image(rgb_image)
    
    def show_menu(self, title, options, selected_index=0):
        """显示菜单"""
        # 根据显示类型选择不同的实现
        if self.display_type == "OLED":
            self._show_menu_oled(title, options, selected_index)
        else:  # LCD
            self._show_menu_lcd(title, options, selected_index)
    
    def _show_menu_oled(self, title, options, selected_index):
        """在OLED上显示菜单"""
        # 清屏
        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        
        # 绘制标题
        font = ImageFont.load_default()
        self.draw.text((0, 0), title, font=font, fill=255)
        self.draw.line([(0, 10), (self.width, 10)], fill=255)
        
        # 绘制选项
        for i, option in enumerate(options):
            y_pos = 15 + i * 10
            if i == selected_index:
                # 绘制选择指示器
                indicator = ">" if self.indicator_frame == 0 else ">>"
                text = indicator + " " + option
            else:
                text = "  " + option
            self.draw.text((0, y_pos), text, font=font, fill=255)
        
        # 显示
        self.oled.image(self.image)
        self.oled.show()
        
        # 更新指示器动画
        current_time = time.time()
        if current_time - self.last_indicator_update > self.indicator_interval:
            self.indicator_frame = (self.indicator_frame + 1) % 2
            self.last_indicator_update = current_time
    
    def _show_menu_lcd(self, title, options, selected_index):
        """在LCD上显示菜单"""
        # 创建新图像
        image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 尝试加载字体
        try:
            title_font = ImageFont.truetype(self.font_path, 24)
            option_font = ImageFont.truetype(self.font_path, 20)
        except:
            print("无法加载字体，使用默认字体")
            title_font = ImageFont.load_default()
            option_font = ImageFont.load_default()
        
        # 绘制标题
        draw.text((10, 10), title, font=title_font, fill=(255, 255, 255))
        draw.line([(10, 40), (self.width-10, 40)], fill=(100, 100, 100), width=2)
        
        # 绘制选项
        for i, option in enumerate(options):
            y_pos = 50 + i * 30
            if i == selected_index:
                # 绘制选中背景
                draw.rectangle([(5, y_pos-2), (self.width-5, y_pos+22)], fill=(0, 0, 100))
                
                # 绘制选择指示器
                indicator = ">" if self.indicator_frame == 0 else ">>"
                text = indicator + " " + option
            else:
                text = "  " + option
            
            draw.text((10, y_pos), text, font=option_font, fill=(255, 255, 255))
        
        # 显示
        self._display_image(image)
        
        # 更新指示器动画
        current_time = time.time()
        if current_time - self.last_indicator_update > self.indicator_interval:
            self.indicator_frame = (self.indicator_frame + 1) % 2
            self.last_indicator_update = current_time
    
    def update_menu_selection(self, direction):
        """更新菜单选择，direction为1表示向下，-1表示向上"""
        # 更新当前选择的索引
        self.current_menu_index += direction
        
        # 确保索引在有效范围内
        if self.current_menu_index < 0:
            self.current_menu_index = 0
        # 上限检查会在实际显示菜单时进行
        
        return self.current_menu_index
    
    def wait_for_menu_selection(self, options, controller, timeout=None):
        """等待用户在菜单中进行选择"""
        num_options = len(options)
        if num_options == 0:
            return -1
        
        selected = 0
        start_time = time.time()
        
        while True:
            # 检查超时
            if timeout and time.time() - start_time > timeout:
                return -1
            
            # 检查按钮1（向下移动）
            if controller.check_button_press(1):
                selected = (selected + 1) % num_options
                time.sleep(0.2)  # 防抖动
            
            # 检查按钮2（确认选择）
            if controller.check_button_press(2):
                return selected
            
            # 更新菜单显示
            self.current_menu_index = selected
            time.sleep(0.05)  # 减少CPU使用率

    def show_text_oled(self, text, corner_text=None):
        """在OLED上显示文本，可选择在右上角显示提示"""
        try:
            # 清屏
            self.clear()
            
            # 确保我们有图像和绘图对象
            if self.display_type == "OLED":
                self.image = Image.new("1", (self.width, self.height))
                self.draw = ImageDraw.Draw(self.image)
            
            # 绘制主文本
            font = ImageFont.load_default()
            
            # 分割文本行
            lines = text.split('\n')
            y_offset = 0
            
            for line in lines:
                self.draw.text((0, y_offset), line, font=font, fill=255)
                y_offset += 10  # 行间距
            
            # 如果有右上角提示，则显示
            if corner_text:
                # 计算文本宽度以放置在右上角
                corner_width = font.getlength(corner_text)
                self.draw.text(
                    (128 - corner_width - 2, 0),  # 右上角位置，微调2像素
                    corner_text,
                    font=font,
                    fill=255
                )
            
            # 显示
            self.oled.image(self.image)
            self.oled.show()
        except Exception as e:
            print(f"OLED显示文本出错: {e}")
            import traceback
            traceback.print_exc()

    def wait_for_button_with_text(self, controller, text, corner_text="▶按钮1"):
        """显示文本并等待按钮点击，右上角显示提示"""
        # 显示文本和角落提示
        self.show_text_oled(text, corner_text=corner_text)
        
        # 等待按钮按下
        controller.wait_for_specific_button(1)