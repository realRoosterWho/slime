import os
import shutil
import time
from typing import Optional
from PIL import Image

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..photo_voice_utils import PhotoVoiceManager

class TakeNewPhotoState(AbstractState):
    """拍摄新照片状态 - 支持拍照+语音并行"""
    
    def __init__(self):
        super().__init__(DeriveState.TAKE_NEW_PHOTO)
    
    def execute(self, context) -> None:
        """执行拍摄新照片+语音录制逻辑"""
        context.logger.log_step("拍摄新照片+语音", "开始拍摄新照片和语音录制")
        
        try:
            # 创建拍照+语音管理器
            photo_voice_manager = PhotoVoiceManager(context)
            
            # 显示提示信息
            context.oled_display.show_text_oled(
                "新照片+语音模式\n"
                "对准拍摄目标\n"
                "并描述新发现"
            )
            time.sleep(2)
            
            # 执行拍照+语音并行录制
            photo_success, voice_text, error_msg = photo_voice_manager.take_photo_with_voice()
            
            if photo_success:
                # 处理拍照成功的情况
                photo_path = os.path.join(context.get_project_root(), "current_image.jpg")
                if os.path.exists(photo_path):
                    # 保存带时间戳的新照片副本
                    timestamped_path = self._save_new_photo_with_timestamp(context, photo_path)
                    
                    # 在LCD上显示照片
                    img = Image.open(photo_path)
                    context.lcd_display.show_image(img)
                    
                    # 保存照片数据
                    context.set_data('new_photo_path', photo_path)
                    context.set_data('new_timestamped_image', timestamped_path)
                    
                    # 保存语音数据（如果有）
                    if voice_text and len(voice_text.strip()) > 0:
                        context.set_data('new_photo_voice_text', voice_text)
                        context.logger.log_step("新照片语音", f"录制到语音: {voice_text[:50]}...")
                    else:
                        # 使用默认语音描述
                        default_voice = photo_voice_manager.get_fallback_voice_text()
                        context.set_data('new_photo_voice_text', default_voice)
                        context.logger.log_step("新照片语音", "使用默认语音描述")
                    
                    context.logger.log_step("拍摄新照片", f"新照片已保存至: {photo_path}")
                    context.logger.save_image(timestamped_path, 'new_photo')
                    
                    # 显示成功信息
                    voice_status = "有语音" if voice_text else "无语音"
                    display_text = f"新照片+语音完成\n照片: 成功\n语音: {voice_status}\n按BT1继续"
                    
                    context.oled_display.wait_for_button_with_text(
                        context.controller,
                        display_text,
                        context=context
                    )
                    
                else:
                    raise FileNotFoundError("未找到拍摄的照片")
                    
            else:
                # 拍照失败，显示错误信息
                context.logger.log_step("错误", f"拍照+语音失败: {error_msg}")
                context.oled_display.show_text_oled(f"拍照+语音失败\n{error_msg or '未知错误'}\n请重试")
                time.sleep(3)
                context.set_data('new_photo_error', True)
                
        except Exception as e:
            context.logger.log_step("错误", f"拍摄新照片+语音失败: {str(e)}")
            context.oled_display.show_text_oled("拍照+语音失败\n请重试")
            time.sleep(2)
            context.set_data('new_photo_error', True)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        # 如果拍照失败，回到等待新照片状态
        if context.get_data('new_photo_error'):
            return DeriveState.WAIT_FOR_NEW_PHOTO
        
        return DeriveState.ANALYZE_NEW_PHOTO
    
    def _save_new_photo_with_timestamp(self, context, photo_path):
        """保存带时间戳的新照片副本"""
        filename = os.path.basename(photo_path)
        name, ext = os.path.splitext(filename)
        timestamped_filename = f"{name}_new_{context.logger.timestamp}{ext}"
        timestamped_path = os.path.join(context.get_project_root(), timestamped_filename)
        
        # 复制照片
        shutil.copy2(photo_path, timestamped_path)
        
        return timestamped_path 