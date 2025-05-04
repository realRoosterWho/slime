import RPi.GPIO as GPIO
import time
import signal
import sys

class JoystickButtonTest:
    def __init__(self):
        # 定义摇杆引脚
        self.JOYSTICK_PINS = {
            'UP': 17,     # GPIO17
            'DOWN': 27,   # GPIO27
            'LEFT': 22,   # GPIO22
            'RIGHT': 23,  # GPIO23
        }
        
        # 定义独立按钮引脚
        self.BUTTON_PINS = {
            'BTN1': 12,   # GPIO12 (SW6)
            'BTN2': 21    # GPIO21 (SW7)
        }
        
        # 初始化GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 设置摇杆引脚为输入，启用内部上拉电阻
        for pin in self.JOYSTICK_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        # 设置按钮引脚为输入，启用内部上拉电阻
        for pin in self.BUTTON_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        # 存储所有输入状态
        self.joystick_states = {pin: GPIO.input(pin) for pin in self.JOYSTICK_PINS.values()}
        self.button_states = {pin: GPIO.input(pin) for pin in self.BUTTON_PINS.values()}
        
        print("摇杆和按钮测试初始化完成")
        print("\n摇杆引脚映射:")
        for name, pin in self.JOYSTICK_PINS.items():
            print(f"{name}: GPIO{pin}")
        print("\n按钮引脚映射:")
        for name, pin in self.BUTTON_PINS.items():
            print(f"{name}: GPIO{pin}")
    
    def check_inputs(self):
        """检查摇杆和按钮状态"""
        # 检查摇杆
        for name, pin in self.JOYSTICK_PINS.items():
            current_state = GPIO.input(pin)
            if current_state == 0 and self.joystick_states[pin] == 1:
                print(f"\n🕹️ 摇杆 {name}")
            self.joystick_states[pin] = current_state
        
        # 检查按钮
        for name, pin in self.BUTTON_PINS.items():
            current_state = GPIO.input(pin)
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
    if 'controller' in globals():
        controller.cleanup()
    sys.exit(0)

if __name__ == "__main__":
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 创建测试实例
        controller = JoystickButtonTest()
        
        print("\n🔄 测试运行中...")
        print("可以测试摇杆和按钮，按 Ctrl+C 退出")
        
        # 持续检测状态
        while True:
            controller.check_inputs()
            time.sleep(0.1)  # 100ms的检测间隔
            
    except Exception as e:
        print(f"错误: {e}")
        if 'controller' in globals():
            controller.cleanup() 