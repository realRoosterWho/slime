from display_utils import DisplayManager
from stt_utils import SpeechToText
import signal
import sys
import time

def cleanup_handler(signum, frame):
    """清理资源并优雅退出"""
    print("\n🛑 检测到中断信号，正在清理资源...")
    try:
        if 'lcd_display' in globals():
            lcd_display.clear()
        if 'oled_display' in globals():
            oled_display.clear()
        print("✅ 已清理显示资源")
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
        oled_display = DisplayManager("OLED")
        lcd_display = DisplayManager("LCD")
        
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
        
        # 步骤6：清理显示
        print("\n清理显示...")
        oled_display.clear()
        lcd_display.clear()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n测试结束")

if __name__ == "__main__":
    main() 