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
        self.display_type = display_type
        # 设置默认中文字体路径
        self.font_path = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
        if display_type == "LCD":
            self.device = BitBangLCD()  # 使用新的BitBang实现
            self.width = 240
            self.height = 240
        else:
            self._init_oled()
        self.current_menu_index = 0  # 当前菜单选择索引
        self.indicator_frame = 0     # 指示器动画帧
        self.last_indicator_update = time.time()
        self.indicator_interval = 0.5  # 指示器更新间隔（秒）
    
    def _init_oled(self):
        """初始化OLED显示屏"""
        i2c = busio.I2C(board.SCL, board.SDA)
        self.device = SSD1306_I2C(128, 64, i2c, addr=0x3C)
        self.width = 128
        self.height = 64
    
    def _display_image(self, image):
        """统一处理图像显示"""
        if self.display_type == "LCD":
            # 只有LCD需要旋转180度
            rotated_image = image.rotate(180)
            self.device.display(rotated_image)
        else:  # OLED保持原样
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

        # 不需要在这里旋转，因为会在_display_image中处理
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

            if self.display_type == "OLED":
                img = img.convert("1")  # 转换为黑白图像
            
            # 不需要在这里旋转，因为会在_display_image中处理
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
    
    def show_menu(self, items):
        """显示菜单（包含滚动和指示器功能）"""
        # 检查是否需要更新指示器
        current_time = time.time()
        if current_time - self.last_indicator_update >= self.indicator_interval:
            self.indicator_frame = (self.indicator_frame + 1) % 2
            self.last_indicator_update = current_time
            
        # 创建基础图像
        image = Image.new("1" if self.display_type == "OLED" else "RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype(self.font_path, 12)
        except:
            print("警告：无法加载中文字体，将使用默认字体")
            font = ImageFont.load_default()

        # 计算显示范围
        total_items = len(items)
        visible_items = self._calculate_visible_items(total_items, self.current_menu_index)
        
        # 绘制菜单项
        self._draw_menu_items(draw, items, visible_items, font)
        
        # 绘制指示器
        self._draw_activity_indicator(draw)
        
        # 显示图像
        self._display_image(image)

    def _calculate_visible_items(self, total_items, current_index, visible_count=3):
        """计算当前应该显示哪些菜单项
        Returns:
            (start_index, end_index)
        """
        if total_items <= visible_count:
            return (0, total_items)
            
        if current_index == 0:
            return (0, visible_count)
        elif current_index == total_items - 1:
            return (total_items - visible_count, total_items)
        else:
            return (current_index - 1, current_index + 2)

    def _draw_menu_items(self, draw, items, visible_range, font):
        """绘制菜单项"""
        start_idx, end_idx = visible_range
        y = 10
        
        for i in range(start_idx, end_idx):
            if i == self.current_menu_index:
                # 绘制选中项的背景
                draw.rectangle((5, y-2, self.width-5, y+12),
                             fill=255 if self.display_type == "OLED" else "white")
                # 绘制选中项的文本
                draw.text((10, y), items[i], font=font,
                         fill=0 if self.display_type == "OLED" else "black")
            else:
                # 绘制未选中项
                draw.text((10, y), items[i], font=font,
                         fill=255 if self.display_type == "OLED" else "white")
            y += 15

    def _draw_activity_indicator(self, draw):
        """绘制活动指示器"""
        y_offset = -1 if self.indicator_frame % 2 == 0 else 1
        dot_size = 2
        draw.ellipse(
            [120, 2 + y_offset, 120 + dot_size, 2 + dot_size + y_offset],
            fill=255 if self.display_type == "OLED" else "white"
        )

    def menu_up(self):
        """菜单向上选择"""
        if self.current_menu_index > 0:
            self.current_menu_index -= 1
            return True
        return False

    def menu_down(self, total_items):
        """菜单向下选择"""
        if self.current_menu_index < total_items - 1:
            self.current_menu_index += 1
            return True
        return False

    def get_selected_index(self):
        """获取当前选中的索引"""
        return self.current_menu_index

    def show_text_oled(self, text, font_size=12, chars_per_line=9, visible_lines=3):
        """专门为OLED优化的文本显示，支持长文本滚动
        Args:
            text: 要显示的文本
            font_size: 字体大小，默认12
            chars_per_line: 每行字符数，默认9
            visible_lines: 同时显示的行数，默认3
        """
        # 创建新图像
        image = Image.new("1", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype(self.font_path, font_size)
        except:
            print("警告：无法加载中文字体，将使用默认字体")
            font = ImageFont.load_default()

        # 处理文本换行
        if '\n' not in text:
            lines = []
            for i in range(0, len(text), chars_per_line):
                lines.append(text[i:i + chars_per_line])
        else:
            lines = text.split('\n')
        
        # 如果文本行数超过可见行数，需要滚动显示
        total_lines = len(lines)
        if total_lines > visible_lines:
            start_line = 0
            while True:
                # 清空图像
                draw.rectangle((0, 0, self.width, self.height), fill=0)
                
                # 绘制当前可见的行
                y = 10
                for i in range(start_line, min(start_line + visible_lines, total_lines)):
                    draw.text((10, y), lines[i], font=font, fill=255)
                    y += 20  # 行间距
                
                # 绘制滚动指示器
                if start_line > 0:  # 顶部箭头
                    draw.polygon([(120, 5), (123, 2), (126, 5)], fill=255)
                if start_line + visible_lines < total_lines:  # 底部箭头
                    draw.polygon([(120, 59), (123, 62), (126, 59)], fill=255)
                
                self._display_image(image)
                time.sleep(3)  # 每页显示3秒
                
                # 更新起始行
                start_line += visible_lines
                if start_line >= total_lines:
                    start_line = 0
        else:
            # 如果文本行数不超过可见行数，直接显示
            y = 10
            for line in lines:
                draw.text((10, y), line, font=font, fill=255)
                y += 20

            self._display_image(image)

    def show_text_oled_interactive(self, text, font_size=12, chars_per_line=9, visible_lines=3):
        """支持摇杆控制的OLED文本显示
        Args:
            text: 要显示的文本
            font_size: 字体大小，默认12
            chars_per_line: 每行字符数，默认9
            visible_lines: 同时显示的行数，默认3
        """
        # 创建新图像
        image = Image.new("1", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype(self.font_path, font_size)
        except:
            print("警告：无法加载中文字体，将使用默认字体")
            font = ImageFont.load_default()

        # 处理文本换行
        if '\n' not in text:
            lines = []
            for i in range(0, len(text), chars_per_line):
                lines.append(text[i:i + chars_per_line])
        else:
            lines = text.split('\n')
        
        # 如果文本行数超过可见行数，需要滚动显示
        total_lines = len(lines)
        start_line = 0
        
        def draw_current_page():
            """绘制当前页面"""
            # 清空图像
            draw.rectangle((0, 0, self.width, self.height), fill=0)
            
            # 绘制当前可见的行
            y = 10
            for i in range(start_line, min(start_line + visible_lines, total_lines)):
                draw.text((10, y), lines[i], font=font, fill=255)
                y += 20  # 行间距
            
            # 绘制滚动指示器
            if start_line > 0:  # 顶部箭头
                draw.polygon([(120, 5), (123, 2), (126, 5)], fill=255)
            if start_line + visible_lines < total_lines:  # 底部箭头
                draw.polygon([(120, 59), (123, 62), (126, 59)], fill=255)
            
            # 绘制页码
            current_page = (start_line // visible_lines) + 1
            total_pages = (total_lines + visible_lines - 1) // visible_lines
            page_text = f"{current_page}/{total_pages}"
            draw.text((90, 54), page_text, font=font, fill=255)
            
            self._display_image(image)
        
        def scroll_up():
            """向上滚动"""
            nonlocal start_line
            if start_line > 0:
                start_line = max(0, start_line - visible_lines)
                return True
            return False
        
        def scroll_down():
            """向下滚动"""
            nonlocal start_line
            if start_line + visible_lines < total_lines:
                start_line = min(total_lines - visible_lines, start_line + visible_lines)
                return True
            return False
        
        # 返回控制函数
        return {
            'draw': draw_current_page,
            'up': scroll_up,
            'down': scroll_down,
            'total_pages': (total_lines + visible_lines - 1) // visible_lines
        }

    def draw_indicator(self, x, y, frame):
        """绘制活动指示器（跳动的点）
        Args:
            x: x坐标
            y: y坐标
            frame: 动画帧数(0或1)
        """
        image = Image.new("1" if self.display_type == "OLED" else "RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        # 根据帧数决定点的位置（上下跳动）
        y_offset = -1 if frame % 2 == 0 else 1
        
        # 绘制点
        dot_size = 2
        draw.ellipse(
            [x, y + y_offset, x + dot_size, y + dot_size + y_offset],
            fill=255 if self.display_type == "OLED" else "white"
        )
        
        return image

    def show_message(self, message, duration=1):
        """显示临时消息，等待指定时间后自动消失
        Args:
            message: 要显示的消息
            duration: 显示持续时间（秒）
        """
        self.show_text_oled(message)
        time.sleep(duration)

    def show_loading(self, message):
        """显示加载消息（不包含延时）"""
        self.show_text_oled(message)

    def wait_for_button_with_text(self, controller, text, chars_per_line=9):
        """显示文本并等待按钮按下，支持摇杆控制滚动
        Args:
            controller: InputController实例
            text: 要显示的文本
            chars_per_line: 每行字符数
        """
        button_pressed = False
        
        def on_button1(pin):
            nonlocal button_pressed
            button_pressed = True
        
        # 设置文本显示控制器
        text_controller = self.show_text_oled_interactive(text, chars_per_line=chars_per_line)
        text_controller['draw']()
        
        # 保存原有的回调
        original_callbacks = {
            'BTN1': controller.button_callbacks.get('BTN1', {}).get('press'),
            'UP': controller.joystick_callbacks.get('UP'),
            'DOWN': controller.joystick_callbacks.get('DOWN')
        }
        
        # 注册新的回调
        controller.register_button_callback('BTN1', on_button1, 'press')
        
        def on_up():
            if text_controller['up']():
                text_controller['draw']()
                time.sleep(0.2)
        
        def on_down():
            if text_controller['down']():
                text_controller['draw']()
                time.sleep(0.2)
        
        controller.register_joystick_callback('UP', on_up)
        controller.register_joystick_callback('DOWN', on_down)
        
        # 等待按钮按下
        while not button_pressed:
            controller.check_inputs()
            time.sleep(0.1)
        
        # 恢复原有的回调
        controller.register_button_callback('BTN1', original_callbacks['BTN1'], 'press')
        controller.register_joystick_callback('UP', original_callbacks['UP'])
        controller.register_joystick_callback('DOWN', original_callbacks['DOWN'])
        
        time.sleep(0.2)  # 防抖 