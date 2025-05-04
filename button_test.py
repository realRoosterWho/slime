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
            
        # 存储按钮状态
        self.button_states = {pin: GPIO.input(pin) for pin in self.BUTTON_PINS.values()}
        
        print("按钮测试初始化完成")
        print("按钮映射:")
        for name, pin in self.BUTTON_PINS.items():
            print(f"{name}: GPIO{pin}")
    
    def check_buttons(self):
        """检查所有按钮状态"""
        for name, pin in self.BUTTON_PINS.items():
            current_state = GPIO.input(pin)
            # 因为使用上拉电阻，所以0表示按下，1表示释放
            if current_state == 0 and self.button_states[pin] == 1:
                print(f"\n🔘 按钮 {name} 被按下")
            elif current_state == 1 and self.button_states[pin] == 0:
                print(f"\n⚪ 按钮 {name} 被释放")
            self.button_states[pin] = current_state
    
    def cleanup(self):
        """清理GPIO资源"""
        GPIO.cleanup()
        print("\n已清理GPIO资源")

def signal_handler(signum, frame):
    """信号处理函数"""
    print("\n🛑 检测到中断信号，正在清理...")
    if 'button_test' in globals():
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
        
        # 持续检测按钮状态
        while True:
            button_test.check_buttons()
            time.sleep(0.1)  # 100ms的检测间隔
            
    except Exception as e:
        print(f"错误: {e}")
        if 'button_test' in globals():
            button_test.cleanup() 