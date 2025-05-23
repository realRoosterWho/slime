import os
import time
import json
import RPi.GPIO as GPIO
from typing import Dict, Any, Optional

from .derive_logger import DeriveLogger
from .derive_states import DeriveState
from core.display.display_utils import DisplayManager
from core.input.button_utils import InputController

class DeriveContext:
    """漂流状态机的上下文，管理共享数据和资源"""
    
    def __init__(self, initial_text: str):
        """初始化上下文
        
        Args:
            initial_text: 用户输入的初始文本
        """
        # 初始化 GPIO 设置
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 核心组件
        self.logger = DeriveLogger()
        self.oled_display = DisplayManager("OLED")
        self.lcd_display = DisplayManager("LCD")
        self.controller = InputController()
        
        # 初始参数
        self.initial_text = initial_text
        self.response_id = None
        
        # 按钮2长按检测相关变量
        self.btn2_pressed_time = 0
        self.btn2_state = 1
        self.btn2_long_press_threshold = 2.0
        self.return_to_menu = False
        
        # 缓存项目根目录路径
        self._project_root = None
        
        # 共享数据存储
        self.data = {
            'personality': None,
            'greeting': None,
            'photo_description': None,
            'destination_suggestion': None,
            'image_path': None,
            'timestamped_image': None,
            'slime_image': None,
            'slime_description': None,
            'slime_appearance': None,
            'new_photo_description': None,
            'new_image_path': None,
            'new_timestamped_image': None,
            'is_obsession_matched': None,
            'reward_type': None,
            'reward_description': None,
            'reward_text': None,
            'reward_image': None,
            'feedback_text': None,
            'feedback_description': None,
            'feedback_image': None,
            'continue_derive': None,
            'summary': None,
            'summary_image': None,
            'cycle_count': 0,
            'all_rewards': [],
            'slime_attributes': {
                'obsession': None,
                'quirk': None,
                'reflex': None,
                'tone': None
            }
        }
        
        # 设置 Replicate API token
        replicate_api_key = os.getenv("REPLICATE_API_KEY")
        if not replicate_api_key:
            raise Exception("没有找到REPLICATE_API_KEY，请检查.env文件设置！")
        os.environ["REPLICATE_API_TOKEN"] = replicate_api_key
    
    def get_project_root(self) -> str:
        """获取项目根目录路径（缓存版本）"""
        if self._project_root is None:
            self._project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return self._project_root
    
    def check_btn2_long_press(self) -> bool:
        """检测按钮2是否被长按"""
        current_btn2 = GPIO.input(self.controller.BUTTON_PINS['BTN2'])
        current_time = time.time()
        
        # 按钮状态变化：从未按下到按下
        if current_btn2 == 0 and self.btn2_state == 1:
            self.btn2_pressed_time = current_time
            self.btn2_state = 0
        
        # 按钮状态变化：从按下到释放
        elif current_btn2 == 1 and self.btn2_state == 0:
            self.btn2_state = 1
            self.btn2_pressed_time = 0
        
        # 检查是否长按
        elif current_btn2 == 0 and self.btn2_state == 0:
            if current_time - self.btn2_pressed_time >= self.btn2_long_press_threshold:
                print("检测到按钮2长按，准备返回菜单")
                self.oled_display.show_text_oled("正在返回菜单...")
                time.sleep(0.5)
                self.return_to_menu = True
                return True
        
        return False
    
    def cleanup(self):
        """清理资源"""
        try:
            # 清理 GPIO
            GPIO.cleanup()
            
            # 清理其他资源
            self.controller.cleanup()
            self.lcd_display.clear()
            self.oled_display.clear()
            
        except Exception as e:
            print(f"清理过程中出错: {e}")
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """安全获取数据"""
        return self.data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置数据"""
        self.data[key] = value
    
    def get_slime_attribute(self, attribute: str, default: str = None) -> str:
        """获取史莱姆属性"""
        return self.data['slime_attributes'].get(attribute, default)
    
    def set_slime_attribute(self, attribute: str, value: str) -> None:
        """设置史莱姆属性"""
        self.data['slime_attributes'][attribute] = value 