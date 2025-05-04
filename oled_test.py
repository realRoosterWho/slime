from display_utils import DisplayManager
import time

def test_oled():
    # 初始化OLED显示管理器
    print("初始化OLED...")
    oled = DisplayManager("OLED")
    
    # 显示测试文本
    print("显示测试信息...")
    test_text = (
        "OLED测试\n"
        "I2C接口\n"
        "SDA: GPIO 2\n"
        "SCL: GPIO 3"
    )
    
    oled.show_text_oled(test_text)

if __name__ == "__main__":
    try:
        test_oled()
        print("OLED测试运行中... 按Ctrl+C退出")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n程序已退出")
