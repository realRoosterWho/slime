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
        else:
            display_text = "准备拍照\n请按下BT1按钮"
            button_text = "按下BT1按钮拍照"
            log_step = "拍照"
        
        context.oled_display.show_text_oled(display_text)
        
        # 等待用户按下按钮1拍照
        self._wait_for_button(context, button_text)
        
        context.oled_display.show_text_oled("正在拍照...")
        
        # 运行相机脚本拍照
        run_camera_test()
        
        # 查找最新拍摄的照片
        try:
            # 先检查项目根目录是否有照片
            photo_path = os.path.join(context.get_project_root(), "current_image.jpg")
            if not os.path.exists(photo_path):
                raise FileNotFoundError("未找到拍摄的照片")
            
            # 保存带时间戳的照片副本
            timestamped_key = self._save_photo_with_timestamp(context, photo_path, is_new_photo)
            
            # 在LCD上显示照片
            img = Image.open(photo_path)
            context.lcd_display.show_image(img)
            
            context.logger.log_step(log_step, f"{'新' if is_new_photo else ''}照片已保存: {context.get_data(timestamped_key)}")
            
            # 等待用户确认照片
            context.oled_display.show_text_oled("照片已拍摄\n按BT1继续")
            self._wait_for_button(context, "按BT1继续")
            
        except Exception as e:
            error_msg = f"处理{'新' if is_new_photo else ''}照片时出错: {str(e)}"
            context.logger.log_step("错误", error_msg)
            context.oled_display.show_text_oled("照片处理失败\n请重试")
            time.sleep(2)
            # 出错时递归重试
            return self._take_photo_process(context, is_new_photo)
    
    def _save_photo_with_timestamp(self, context, photo_path, is_new_photo=False):
        """保存带时间戳的照片副本"""
        filename = os.path.basename(photo_path)
        suffix = "new" if is_new_photo else ""
        timestamped_filename = self._create_timestamped_filename(context, filename, suffix)
        timestamped_path = os.path.join(context.get_project_root(), timestamped_filename)
        
        # 复制照片
        shutil.copy2(photo_path, timestamped_path)
        
        # 保存到相应的数据键
        if is_new_photo:
            context.set_data('new_image_path', photo_path)
            context.set_data('new_timestamped_image', timestamped_path)
            context.logger.save_image(timestamped_path, 'new_photo')
            return 'new_timestamped_image'
        else:
            context.set_data('image_path', photo_path)
            context.set_data('timestamped_image', timestamped_path)
            context.logger.save_image(timestamped_path, 'original_photo')
            return 'timestamped_image'
    
    def _create_timestamped_filename(self, context, base_filename, suffix=""):
        """创建带时间戳的文件名"""
        name, ext = os.path.splitext(base_filename)
        if suffix:
            return f"{name}_{suffix}_{context.logger.timestamp}{ext}"
        else:
            return f"{name}_{context.logger.timestamp}{ext}"
    
    def _wait_for_button(self, context, text):
        """等待按钮按下"""
        context.oled_display.wait_for_button_with_text(
            context.controller,
            text
        ) 