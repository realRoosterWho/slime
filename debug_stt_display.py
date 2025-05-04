from display_utils import DisplayManager
from stt_utils import SpeechToText
import signal
import sys
import time
import RPi.GPIO as GPIO

def cleanup_handler(signum, frame):
    """清理资源并优雅退出"""
    print("\n🛑 检测到中断信号，正在清理资源...")
    try:
        if 'lcd_display' in globals():
            lcd_display.clear()
        if 'oled_display' in globals():
            oled_display.clear()
        GPIO.cleanup()  # 确保GPIO被正确清理
        print("✅ 已清理显示资源和GPIO")
    except:
        pass
    sys.exit(0)

def main():
    # 设置信号处理
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        # 步骤1：初始化显示设备
        print("初始化显示设备...")
        print("正在初始化OLED...")
        oled_display = DisplayManager("OLED")
        
        print("正在初始化LCD (BitBang模式)...")
        lcd_display = DisplayManager("LCD")  # 现在使用BitBang模式
        print("LCD初始化完成")
        
        # 测试LCD是否正常工作
        print("测试LCD显示...")
        from PIL import Image
        test_image = Image.new('RGB', (240, 240), 'blue')
        lcd_display.show_image(test_image)
        print("LCD测试图像已显示")
        time.sleep(2)
        
        # 步骤2：显示一些测试文本
        print("在OLED上显示测试文本...")
        oled_display.show_text_oled("测试文本", chars_per_line=12)
        time.sleep(2)
        
        # 步骤3：初始化语音识别
        print("\n初始化语音识别模块...")
        stt = SpeechToText()
        
        # 步骤4：进行语音识别测试
        print("\n🎤 请在5秒内说话...")
        user_input = stt.record_and_transcribe(duration=5)
        print(f"\n👂 识别结果: {user_input}")
        
        # 步骤5：在OLED上显示识别结果
        print("\n在OLED上显示识别结果...")
        oled_display.show_text_oled(user_input)
        time.sleep(3)
        
        # 步骤6：在LCD上显示一些内容
        print("\n在LCD上显示测试图像...")
        test_image = Image.new('RGB', (240, 240), 'red')
        lcd_display.show_image(test_image)
        time.sleep(3)
        
        # 步骤7：清理显示
        print("\n清理显示...")
        oled_display.clear()
        lcd_display.clear()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n测试结束")
        GPIO.cleanup()  # 确保在结束时清理GPIO

if __name__ == "__main__":
    main() 