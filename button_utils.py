import RPi.GPIO as GPIO
import time
from typing import Dict, Callable, Optional

class InputController:
    """输入控制器类，用于管理摇杆和按钮输入"""
    
    def __init__(self):
        # 定义摇杆引脚
        self.JOYSTICK_PINS = {
            'UP': 17,     # GPIO17
            'LEFT': 27,   # GPIO27
            'RIGHT': 22,  # GPIO22
            'DOWN': 23,   # GPIO23
        }
        
        # 定义独立按钮引脚
        self.BUTTON_PINS = {
            'BTN1': 12,   # GPIO12 (SW6)
            'BTN2': 21    # GPIO21 (SW7)
        }
        
        # 初始化GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 设置所有引脚为输入，启用内部上拉电阻
        for pin in {**self.JOYSTICK_PINS, **self.BUTTON_PINS}.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        # 存储所有输入状态
        self.joystick_states = {pin: GPIO.input(pin) for pin in self.JOYSTICK_PINS.values()}
        self.button_states = {pin: GPIO.input(pin) for pin in self.BUTTON_PINS.values()}
        
        # 回调函数字典
        self.joystick_callbacks: Dict[str, Callable] = {}
        self.button_callbacks: Dict[str, Dict[str, Callable]] = {
            'press': {},
            'release': {}
        }
    
    def register_joystick_callback(self, direction: str, callback: Callable):
        """注册摇杆回调函数
        Args:
            direction: 方向('UP', 'DOWN', 'LEFT', 'RIGHT')
            callback: 回调函数
        """
        if direction in self.JOYSTICK_PINS:
            self.joystick_callbacks[direction] = callback
    
    def register_button_callback(self, button: str, callback: Callable, event_type: str = 'press'):
        """注册按钮回调函数
        Args:
            button: 按钮名称('BTN1', 'BTN2')
            callback: 回调函数
            event_type: 事件类型('press' 或 'release')
        """
        if button in self.BUTTON_PINS and event_type in self.button_callbacks:
            self.button_callbacks[event_type][button] = callback
    
    def check_inputs(self) -> Dict[str, bool]:
        """检查所有输入状态
        Returns:
            包含所有输入当前状态的字典
        """
        input_states = {}
        
        # 检查摇杆
        for name, pin in self.JOYSTICK_PINS.items():
            current_state = GPIO.input(pin)
            if current_state == 0 and self.joystick_states[pin] == 1:
                if name in self.joystick_callbacks:
                    self.joystick_callbacks[name]()
            input_states[f"JOY_{name}"] = current_state == 0
            self.joystick_states[pin] = current_state
        
        # 检查按钮
        for name, pin in self.BUTTON_PINS.items():
            current_state = GPIO.input(pin)
            # 按下事件
            if current_state == 0 and self.button_states[pin] == 1:
                if name in self.button_callbacks['press']:
                    self.button_callbacks['press'][name]()
            # 释放事件
            elif current_state == 1 and self.button_states[pin] == 0:
                if name in self.button_callbacks['release']:
                    self.button_callbacks['release'][name]()
            input_states[name] = current_state == 0
            self.button_states[pin] = current_state
            
        return input_states
    
    def cleanup(self):
        """清理GPIO资源"""
        GPIO.cleanup()

# 使用示例
if __name__ == "__main__":
    def on_joystick(direction):
        return lambda: print(f"\n🕹️ 摇杆 {direction}")
    
    def on_button_press(button):
        return lambda: print(f"\n🔘 按钮 {button} 被按下")
    
    def on_button_release(button):
        return lambda: print(f"\n⚪ 按钮 {button} 被释放")
    
    try:
        controller = InputController()
        
        # 注册回调函数
        for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            controller.register_joystick_callback(direction, on_joystick(direction))
        
        for btn in ['BTN1', 'BTN2']:
            controller.register_button_callback(btn, on_button_press(btn), 'press')
            controller.register_button_callback(btn, on_button_release(btn), 'release')
        
        print("输入控制器测试运行中...")
        print("按 Ctrl+C 退出")
        
        while True:
            controller.check_inputs()
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    finally:
        controller.cleanup() 