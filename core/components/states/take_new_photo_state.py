import os
import shutil
import time
from typing import Optional
from PIL import Image

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import run_camera_test

class TakeNewPhotoState(AbstractState):
    """拍摄新照片状态"""
    
    def __init__(self):
        super().__init__(DeriveState.TAKE_NEW_PHOTO)
    
    def execute(self, context) -> None:
        """执行拍摄新照片逻辑"""
        context.logger.log_step("拍摄新照片", "开始拍摄新照片")
        
        # 显示拍照提示
        context.oled_display.show_text_oled("准备拍摄新照片\n请按下BT1按钮")
        
        # 等待用户按下按钮1拍照
        self._wait_for_button(context, "按下BT1按钮拍照")
        
        context.oled_display.show_text_oled("正在拍照...")
        
        try:
            # 生成文件名
            filename = f"new_photo_{context.logger.timestamp}.jpg"
            
            # 直接拍照到日志目录
            photo_path = run_camera_test(save_path=context.logger.log_dir, filename=filename)
            
            if not photo_path or not os.path.exists(photo_path):
                raise FileNotFoundError("未找到拍摄的照片")
            
            # 在LCD上显示照片
            img = Image.open(photo_path)
            context.lcd_display.show_image(img)
            
            # 将新照片路径保存到上下文
            context.set_data('new_photo_path', photo_path)
            context.set_data('new_timestamped_image', photo_path)
            
            context.logger.log_step("拍摄新照片", f"新照片已保存至: {photo_path}")
            context.logger.save_image(photo_path, 'new_photo')
            
            # 等待用户确认照片
            result = context.oled_display.wait_for_button_with_text(
                context.controller,
                "新照片已拍摄\n按BT1继续",
                context=context  # 传入context用于长按检测
            )
            
            # 检查是否是长按返回菜单
            if result == 2:
                context.logger.log_step("用户操作", "用户长按按钮2返回菜单")
            
        except Exception as e:
            context.logger.log_step("错误", f"拍摄新照片失败: {str(e)}")
            context.oled_display.show_text_oled("拍照失败\n请重试")
            time.sleep(2)
            
            # 拍照失败，设置错误标志
            context.set_data('new_photo_error', True)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        # 如果拍照失败，回到等待新照片状态
        if context.get_data('new_photo_error'):
            return DeriveState.WAIT_FOR_NEW_PHOTO
        
        return DeriveState.ANALYZE_NEW_PHOTO
    
    def _wait_for_button(self, context, text):
        """等待按钮按下"""
        context.oled_display.wait_for_button_with_text(
            context.controller,
            text
        ) 