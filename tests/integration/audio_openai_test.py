import os
import sys
import time
import signal
from openai import OpenAI
from dotenv import load_dotenv
from stt_utils import SpeechToText
import board
import busio
from PIL import Image, ImageDraw, ImageFont
from adafruit_ssd1306 import SSD1306_I2C

# 加载环境变量
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SimpleOLED:
    def __init__(self):
        # 初始化I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        # 初始化OLED显示屏 (128x64)
        self.display = SSD1306_I2C(128, 64, i2c, addr=0x3C)
        self.width = 128
        self.height = 64
        # 设置默认中文字体
        self.font_path = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
        
    def show_text(self, text, chars_per_line=12):
        """显示文本，支持中文"""
        # 创建空白图像
        image = Image.new('1', (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        try:
            # 加载中文字体
            font = ImageFont.truetype(self.font_path, 12)
        except:
            print("警告：无法加载中文字体，使用默认字体")
            font = ImageFont.load_default()
            
        # 文本换行处理
        if '\n' not in text:
            lines = []
            for i in range(0, len(text), chars_per_line):
                lines.append(text[i:i + chars_per_line])
            text = '\n'.join(lines)
            
        # 绘制文本
        y = 10
        for line in text.split('\n'):
            draw.text((10, y), line, font=font, fill=255)
            y += 20
            
        # 显示到OLED
        self.display.image(image)
        self.display.show()
        
    def clear(self):
        """清空显示"""
        self.display.fill(0)
        self.display.show()

def chat_with_gpt(messages):
    """与GPT对话"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT对话出错: {e}")
        return "对不起，我现在无法回答。"

def cleanup_handler(signum, frame):
    """清理资源并优雅退出"""
    print("\n🛑 检测到中断信号，正在清理资源...")
    try:
        oled.clear()
        print("✅ 已清理显示资源")
    except:
        pass
    sys.exit(0)

def main():
    global oled
    
    # 设置信号处理
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        # 初始化OLED
        print("初始化OLED显示屏...")
        oled = SimpleOLED()
        
        # 初始化语音识别
        print("初始化语音识别模块...")
        stt = SpeechToText()
        
        # 显示欢迎信息
        oled.show_text("你好！\n我是AI助手")
        time.sleep(2)
        
        # 对话历史
        messages = [
            {"role": "system", "content": "你是一个友好的AI助手，请用简短的语言回答，最多15个字。"}
        ]
        
        while True:
            # 提示用户说话
            oled.show_text("请说话...\n(5秒)")
            print("\n🎤 请在5秒内说话...")
            
            # 录音并识别
            user_input = stt.record_and_transcribe(duration=5)
            print(f"\n👂 识别结果: {user_input}")
            
            # 显示识别结果
            oled.show_text(f"你说:\n{user_input}")
            time.sleep(1)
            
            # 添加用户输入到对话历史
            messages.append({"role": "user", "content": user_input})
            
            # 获取AI回复
            print("\n🤖 AI思考中...")
            oled.show_text("思考中...")
            ai_response = chat_with_gpt(messages)
            print(f"🤖 AI回复: {ai_response}")
            
            # 显示AI回复
            oled.show_text(ai_response)
            time.sleep(3)
            
            # 添加AI回复到对话历史
            messages.append({"role": "assistant", "content": ai_response})
            
            # 是否继续对话
            oled.show_text("继续对话?\n按Ctrl+C退出")
            time.sleep(2)
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        oled.clear()

if __name__ == "__main__":
    main() 