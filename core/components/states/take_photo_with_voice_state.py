import os
import shutil
import time
from typing import Optional
from PIL import Image

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..photo_voice_utils import PhotoVoiceManager

class TakePhotoWithVoiceState(AbstractState):
    """拍照+语音状态 - 15秒倒计时拍照+并行语音录制"""
    
    def __init__(self):
        super().__init__(DeriveState.TAKE_PHOTO_WITH_VOICE)
    
    def execute(self, context) -> None:
        """执行拍照+语音录制逻辑"""
        context.logger.log_step("拍照+语音状态", "开始拍照+语音录制流程")
        
        try:
            # 创建拍照+语音管理器
            photo_voice_manager = PhotoVoiceManager(context)
            
            # 执行拍照+语音录制
            photo_success, voice_text, error_msg = photo_voice_manager.take_photo_with_voice()
            
            if photo_success:
                # 拍照成功，处理照片
                self._handle_photo_success(context, voice_text or photo_voice_manager.get_fallback_voice_text())
            else:
                # 拍照失败，记录错误并重试
                context.logger.log_step("拍照+语音错误", error_msg or "拍照失败")
                self._handle_photo_failure(context, error_msg)
            
        except Exception as e:
            context.logger.log_step("错误", f"拍照+语音状态执行失败: {str(e)}")
            self._handle_photo_failure(context, str(e))
    
    def _handle_photo_success(self, context, voice_text: str):
        """处理拍照成功的情况"""
        try:
            # 查找拍摄的照片
            photo_path = os.path.join(context.get_project_root(), "current_image.jpg")
            if not os.path.exists(photo_path):
                raise FileNotFoundError("未找到拍摄的照片")
            
            # 保存带时间戳的照片副本
            timestamped_path = self._save_photo_with_timestamp(context, photo_path)
            
            # 在LCD上显示照片
            img = Image.open(photo_path)
            context.lcd_display.show_image(img)
            
            # 保存照片和语音数据
            context.set_data('image_path', photo_path)
            context.set_data('timestamped_image', timestamped_path)
            context.set_data('photo_voice_text', voice_text)  # 保存拍照时的语音
            
            context.logger.log_step("拍照+语音成功", f"照片已保存: {photo_path}")
            context.logger.log_step("拍照语音", f"语音内容: {voice_text}")
            context.logger.save_image(timestamped_path, 'photo_with_voice')
            
            # 显示拍照结果
            self._show_photo_result(context, voice_text)
            
        except Exception as e:
            context.logger.log_step("错误", f"处理拍照结果失败: {str(e)}")
            self._handle_photo_failure(context, str(e))
    
    def _handle_photo_failure(self, context, error_msg: str):
        """处理拍照失败的情况"""
        context.oled_display.show_text_oled(
            "拍照失败\n请重试\n\n按BT1重新拍照"
        )
        
        # 等待用户选择重试
        result = context.oled_display.wait_for_button_with_text(
            context.controller,
            "拍照失败\n按BT1重试\n按BT2跳过",
            context=context
        )
        
        if result == 2:  # 长按返回菜单
            context.logger.log_step("用户操作", "用户长按返回菜单")
        elif hasattr(context.controller, 'last_button'):
            if context.controller.last_button == 'BTN1':
                # 用户选择重试，设置重试标志
                context.set_data('photo_voice_retry', True)
            elif context.controller.last_button == 'BTN2':
                # 用户选择跳过，使用默认数据
                self._use_default_photo_data(context)
    
    def _use_default_photo_data(self, context):
        """使用默认照片数据（当拍照失败时）"""
        default_voice = "这是一个特别的地方，虽然没能拍照，但感受到了它的美好"
        context.set_data('photo_voice_text', default_voice)
        context.set_data('photo_failed', True)
        
        context.logger.log_step("使用默认数据", "拍照失败，使用默认语音描述")
        
        context.oled_display.show_text_oled(
            "使用默认描述\n继续流程\n\n按BT1继续"
        )
        
        context.oled_display.wait_for_button_with_text(
            context.controller,
            "准备继续...",
            context=context
        )
    
    def _show_photo_result(self, context, voice_text: str):
        """显示拍照+语音结果"""
        # 截断过长的语音文本用于显示
        display_voice = voice_text
        if len(display_voice) > 40:
            display_voice = display_voice[:37] + "..."
        
        result_text = f"拍照完成！\n\n语音: {display_voice}\n\n按BT1继续"
        
        # 等待用户确认
        context.oled_display.wait_for_button_with_text(
            context.controller,
            result_text,
            context=context
        )
    
    def _save_photo_with_timestamp(self, context, photo_path: str) -> str:
        """保存带时间戳的照片副本"""
        filename = os.path.basename(photo_path)
        name, ext = os.path.splitext(filename)
        timestamped_filename = f"{name}_with_voice_{context.logger.timestamp}{ext}"
        timestamped_path = os.path.join(context.get_project_root(), timestamped_filename)
        
        # 复制照片
        shutil.copy2(photo_path, timestamped_path)
        
        return timestamped_path
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        # 如果需要重试
        if context.get_data('photo_voice_retry'):
            context.set_data('photo_voice_retry', False)  # 清除重试标志
            return DeriveState.TAKE_PHOTO_WITH_VOICE  # 重新执行当前状态
        
        # 正常情况下进入处理阶段
        return DeriveState.PROCESS_PHOTO_VOICE 