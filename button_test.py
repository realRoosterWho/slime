import RPi.GPIO as GPIO
import time
import signal
import sys

class ButtonTest:
    def __init__(self):
        # 定义按钮引脚
        self.BUTTON_PINS = {
            'BTN1': 17,  # GPIO17
            'BTN2': 27,  # GPIO27
            'BTN3': 12,  # GPIO12
            'BTN4': 21   # GPIO21
        }
        
        # 初始化GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 设置所有按钮为输入，启用内部上拉电阻
        for pin in self.BUTTON_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        # 为每个按钮添加事件检测
        for name, pin in self.BUTTON_PINS.items():
            GPIO.add_event_detect(pin, GPIO.FALLING, 
                                callback=lambda x, btn=name: self.button_callback(btn), 
                                bouncetime=300)
        
        print("按钮测试初始化完成")
        print("按钮映射:")
        for name, pin in self.BUTTON_PINS.items():
            print(f"{name}: GPIO{pin}")
    
    def button_callback(self, button_name):
        """按钮回调函数"""
        print(f"\n🔘 按钮 {button_name} 被按下")
        
    def cleanup(self):
        """清理GPIO资源"""
        GPIO.cleanup()
        print("\n已清理GPIO资源")

def signal_handler(signum, frame):
    """信号处理函数"""
    print("\n🛑 检测到中断信号，正在清理...")
    button_test.cleanup()
    sys.exit(0)

if __name__ == "__main__":
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 创建按钮测试实例
        button_test = ButtonTest()
        
        print("\n🔄 按钮测试运行中...")
        print("按下任意按钮测试，按 Ctrl+C 退出")
        
        # 保持程序运行
        while True:
            time.sleep(0.1)
            
    except Exception as e:
        print(f"错误: {e}")
        button_test.cleanup() 