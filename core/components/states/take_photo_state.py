import os
import shutil
import time
from typing import Optional
from PIL import Image

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import run_camera_test

class TakePhotoState(AbstractState):
    """拍照状态"""
    
    def __init__(self):
        super().__init__(DeriveState.TAKE_PHOTO)
    
    def execute(self, context) -> None:
        """执行拍照逻辑"""
        self._take_photo_process(context, is_new_photo=False)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：分析照片"""
        return DeriveState.ANALYZE_PHOTO
    
    def _take_photo_process(self, context, is_new_photo=False):
        """统一的拍照处理方法"""
        # 根据是否为新照片显示不同的提示文本
        if is_new_photo:
            display_text = "准备拍摄新照片\n请按下BT1按钮"
            button_text = "按下BT1按钮拍照"
            log_step = "新照片"
            filename = f"new_photo_{context.logger.timestamp}.jpg"
        else:
            display_text = "准备拍照\n请按下BT1按钮"
            button_text = "按下BT1按钮拍照"
            log_step = "拍照"
            filename = f"photo_{context.logger.timestamp}.jpg"
        
        context.oled_display.show_text_oled(display_text)
        
        # 等待用户按下按钮1拍照
        self._wait_for_button(context, button_text)
        
        context.oled_display.show_text_oled("正在拍照...")
        
        # 直接将照片保存到日志目录
        try:
            # 直接拍照到日志目录
            photo_path = run_camera_test(save_path=context.logger.log_dir, filename=filename)
            
            if not photo_path or not os.path.exists(photo_path):
                raise FileNotFoundError("未找到拍摄的照片")
            
            # 在LCD上显示照片
            img = Image.open(photo_path)
            context.lcd_display.show_image(img)
            
            # 保存照片路径到上下文
            if is_new_photo:
                context.set_data('new_image_path', photo_path)
                context.set_data('new_timestamped_image', photo_path)
                context.logger.save_image(photo_path, 'new_photo')
            else:
                context.set_data('image_path', photo_path)
                context.set_data('timestamped_image', photo_path)
                context.logger.save_image(photo_path, 'original_photo')
            
            context.logger.log_step(log_step, f"{'新' if is_new_photo else ''}照片已保存: {photo_path}")
            
            # 等待用户确认照片
            result = context.oled_display.wait_for_button_with_text(
                context.controller,
                "照片已拍摄\n按BT1继续",
                context=context  # 传入context用于长按检测
            )
            
            # 检查是否是长按返回菜单
            if result == 2:
                context.logger.log_step("用户操作", "用户长按按钮2返回菜单")
            
        except Exception as e:
            error_msg = f"处理{'新' if is_new_photo else ''}照片时出错: {str(e)}"
            context.logger.log_step("错误", error_msg)
            context.oled_display.show_text_oled("照片处理失败\n请重试")
            time.sleep(2)
            # 出错时递归重试
            return self._take_photo_process(context, is_new_photo)
    
    def _wait_for_button(self, context, text):
        """等待按钮按下"""
        context.oled_display.wait_for_button_with_text(
            context.controller,
            text
        ) 