from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..voice_input_utils import VoiceInputManager

class VoiceInputMoodState(AbstractState):
    """初始心情语音输入状态"""
    
    def __init__(self):
        super().__init__(DeriveState.VOICE_INPUT_MOOD)
    
    def execute(self, context) -> None:
        """执行语音录制流程"""
        context.logger.log_step("语音输入状态", "开始语音输入心情流程")
        
        try:
            # 创建语音输入管理器
            voice_manager = VoiceInputManager(context)
            
            # 显示欢迎信息
            self._show_welcome_message(context)
            
            # 等待用户选择
            user_choice = self._get_user_choice(context)
            
            if user_choice == 'voice_input':
                # 用户选择语音输入
                success = self._handle_voice_input(context, voice_manager)
                if not success:
                    # 语音输入失败，使用默认心情
                    self._use_default_mood(context, voice_manager)
            
            elif user_choice == 'default_mood':
                # 用户选择默认心情
                self._use_default_mood(context, voice_manager)
                
            elif user_choice == 'menu':
                # 用户选择返回菜单
                context.logger.log_step("用户操作", "用户选择返回菜单")
                return
            
            context.logger.log_step("语音输入状态", "语音输入流程完成")
            
        except Exception as e:
            context.logger.log_step("错误", f"语音输入状态执行失败: {str(e)}")
            
            # 发生错误时使用默认心情
            voice_manager = VoiceInputManager(context)
            self._use_default_mood(context, voice_manager)
    
    def _show_welcome_message(self, context):
        """显示欢迎信息"""
        context.oled_display.show_text_oled(
            "欢迎来到漂流世界！"
        )
        context.sleep(2)
    
    def _get_user_choice(self, context) -> str:
        """获取用户选择"""
        # 显示选择界面
        result = context.oled_display.wait_for_button_with_text(
            context.controller,
            "语音输入心情\n"
            "按BT1 - 语音输入\n"
            "按BT2 - 使用默认",
            context=context
        )
        
        # 检查是否长按返回菜单
        if result == 2:
            return 'menu'
        
        # 检查具体按键
        if hasattr(context.controller, 'last_button'):
            if context.controller.last_button == 'BTN1':
                return 'voice_input'
            elif context.controller.last_button == 'BTN2':
                return 'default_mood'
        
        # 默认选择语音输入
        return 'voice_input'
    
    def _handle_voice_input(self, context, voice_manager) -> bool:
        """处理语音输入，返回是否成功"""
        try:
            context.logger.log_step("语音录制", "开始录音")
            
            # 录制语音（内部已包含重录逻辑）
            success, raw_text, error_msg = voice_manager.record_mood_voice(duration=15)
            
            if success and raw_text:
                # 验证语音结果
                if voice_manager.validate_voice_result(raw_text):
                    # 保存原始语音文本，准备交给下一个状态处理
                    context.set_data('raw_voice_text', raw_text)
                    context.logger.log_step("语音输入成功", f"获取到有效语音文本: {raw_text[:50]}...")
                    return True
                else:
                    # 语音内容无效，使用默认心情
                    context.logger.log_step("语音验证失败", "语音内容过短或无效，使用默认心情")
                    return False
            else:
                # 录音失败或用户取消，使用默认心情
                context.logger.log_step("语音输入失败", error_msg or "录音失败，使用默认心情")
                return False
                
        except Exception as e:
            error_msg = f"录音异常: {str(e)}"
            context.logger.log_step("语音错误", error_msg)
            return False
    
    def _use_default_mood(self, context, voice_manager):
        """使用默认心情"""
        default_mood = voice_manager.get_default_mood_text()
        context.set_data('raw_voice_text', default_mood)
        context.set_data('is_voice_input', False)  # 标记不是语音输入
        
        context.logger.log_step("使用默认心情", f"默认心情文本: {default_mood[:50]}...")
        
        # 显示默认心情
        context.oled_display.show_text_oled(
            "使用默认心情\n"
            "已为你选择一个\n"
            "轻松愉快的心情状态"
        )
        context.sleep(2)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        # 检查是否有语音文本（包括默认文本）
        raw_text = context.get_data('raw_voice_text')
        if raw_text:
            return DeriveState.PROCESS_MOOD
        else:
            # 没有文本，返回菜单
            return DeriveState.EXIT 