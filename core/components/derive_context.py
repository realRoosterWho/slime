import os
import time
import json
import RPi.GPIO as GPIO
from typing import Dict, Any, Optional

from .derive_logger import DeriveLogger
from .derive_states import DeriveState
from .performance_optimizer import global_resource_manager, global_optimizer
from core.display.display_utils import DisplayManager
from core.input.button_utils import InputController

class DeriveContext:
    """漂流状态机的上下文，管理共享数据和资源"""
    
    def __init__(self, initial_text: str):
        """初始化上下文
        
        Args:
            initial_text: 用户输入的初始文本
        """
        # 集成性能优化器和资源管理器
        self.optimizer = global_optimizer
        self.resource_manager = global_resource_manager
        
        # 初始化 GPIO 设置
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 核心组件 - 使用资源管理器
        self.logger = DeriveLogger()
        self.resource_manager.acquire_resource("logger", self.logger)
        
        self.oled_display = DisplayManager("OLED")
        self.resource_manager.acquire_resource("oled_display", self.oled_display)
        
        self.lcd_display = DisplayManager("LCD")
        self.resource_manager.acquire_resource("lcd_display", self.lcd_display)
        
        self.controller = InputController()
        self.resource_manager.acquire_resource("controller", self.controller)
        
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
            'cycle_count': 1,
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
        
        # 记录初始化完成
        self.logger.log_step("初始化", "DeriveContext 初始化完成")
    
    def get_project_root(self) -> str:
        """获取项目根目录路径（缓存版本）"""
        if self._project_root is None:
            self._project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return self._project_root
    
    def check_btn2_long_press(self) -> bool:
        """检测按钮2是否被长按 - 优化版本"""
        try:
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
                    self.logger.log_step("用户操作", "检测到按钮2长按，返回菜单")
                    return True
            
            return False
            
        except Exception as e:
            # 按钮检测出错，记录日志但不影响主流程
            self.logger.log_step("按钮检测错误", f"按钮2长按检测出错: {str(e)}")
            return False
    
    def should_return_to_menu(self) -> bool:
        """检查是否应该返回菜单"""
        # 检查按钮2长按
        if self.check_btn2_long_press():
            return True
        
        # 检查返回菜单标志
        return self.return_to_menu
    
    def sleep(self, seconds: float) -> None:
        """等待指定时间，期间检查按钮状态 - 优化版本"""
        if seconds <= 0:
            return
        
        end_time = time.time() + seconds
        check_interval = min(0.1, seconds / 10)  # 动态调整检查间隔
        
        while time.time() < end_time:
            if self.check_btn2_long_press():
                break
            time.sleep(check_interval)
    
    def cleanup(self):
        """清理资源 - 优化版本"""
        try:
            self.logger.log_step("清理资源", "开始清理DeriveContext资源")
            
            # 设置返回菜单标志，停止所有操作
            self.return_to_menu = True
            
            # 使用资源管理器清理所有资源
            self.resource_manager.release_all()
            
            # 清理 GPIO
            try:
                GPIO.cleanup()
                print("🧹 GPIO 已清理")
            except Exception as e:
                print(f"清理GPIO时出错: {e}")
            
            # 清理优化器缓存
            try:
                self.optimizer.clear_cache("derive")
                print("🧹 缓存已清理")
            except Exception as e:
                print(f"清理缓存时出错: {e}")
            
            print("✅ DeriveContext 资源清理完成")
            
        except Exception as e:
            print(f"清理过程中出错: {e}")
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """安全获取数据"""
        return self.data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置数据"""
        self.data[key] = value
        
        # 对重要数据进行缓存
        if key in ['slime_attributes', 'personality', 'cycle_count']:
            cache_key = f"derive_data_{key}_{hash(str(value))}"
            self.optimizer.set_cache(cache_key, value)
    
    def get_slime_attribute(self, attribute: str, default: str = None) -> str:
        """获取史莱姆属性"""
        return self.data['slime_attributes'].get(attribute, default)
    
    def set_slime_attribute(self, attribute: str, value: str) -> None:
        """设置史莱姆属性"""
        self.data['slime_attributes'][attribute] = value
        
        # 缓存属性更新
        cache_key = f"slime_attr_{attribute}_{hash(value)}"
        self.optimizer.set_cache(cache_key, value)
        
        self.logger.log_step("属性设置", f"设置史莱姆属性 {attribute}: {value}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            'resource_count': len(self.resource_manager.active_resources),
            'cache_size': len(self.optimizer.memory_cache),
            'failure_counts': dict(self.optimizer.failure_counts),
            'api_call_times': dict(self.optimizer.api_call_times),
            'cycle_count': self.get_data('cycle_count', 0),
            'total_rewards': len(self.get_data('all_rewards', []))
        }
    
    def log_performance_stats(self) -> None:
        """记录性能统计信息"""
        stats = self.get_performance_stats()
        self.logger.log_step("性能统计", f"资源: {stats['resource_count']}, 缓存: {stats['cache_size']}, 循环: {stats['cycle_count']}")
    
    def validate_state(self) -> bool:
        """验证上下文状态的完整性"""
        try:
            # 检查核心组件
            if not hasattr(self, 'logger') or not self.logger:
                print("❌ Logger 未正确初始化")
                return False
            
            if not hasattr(self, 'oled_display') or not self.oled_display:
                print("❌ OLED显示器未正确初始化")
                return False
            
            if not hasattr(self, 'lcd_display') or not self.lcd_display:
                print("❌ LCD显示器未正确初始化")
                return False
            
            if not hasattr(self, 'controller') or not self.controller:
                print("❌ 控制器未正确初始化")
                return False
            
            # 检查数据完整性
            required_keys = ['slime_attributes', 'cycle_count', 'all_rewards']
            for key in required_keys:
                if key not in self.data:
                    print(f"❌ 数据缺失: {key}")
                    return False
            
            print("✅ Context 状态验证通过")
            return True
            
        except Exception as e:
            print(f"❌ Context 状态验证失败: {e}")
            return False 