from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils

class AskPhotoState(AbstractState):
    """询问拍照状态"""
    
    def __init__(self):
        super().__init__(DeriveState.ASK_PHOTO)
    
    def execute(self, context) -> None:
        """执行询问拍照逻辑"""
        # 使用聊天工具生成询问语句
        chat_utils = DeriveChatUtils(context.response_id)
        
        photo_question = chat_utils.generate_text('photo_question', text=context.get_data('personality'))
        context.response_id = chat_utils.response_id
        
        context.logger.log_step("询问拍照", photo_question)
        
        # 显示史莱姆的询问
        context.oled_display.show_text_oled(f"史莱姆说：\n{photo_question}")
        context.sleep(3)
        
        # 提供拍照模式选择
        self._choose_photo_mode(context)
    
    def _choose_photo_mode(self, context):
        """让用户选择拍照模式"""
        # 等待用户选择拍照模式
        result = context.oled_display.wait_for_button_with_text(
            context.controller,
            "选择拍照模式：\n\nBT1 - 快速拍照\nBT2 - 拍照+语音",
            context=context
        )
        
        # 检查是否是长按返回菜单
        if result == 2:
            context.logger.log_step("用户操作", "用户长按返回菜单")
            return
        
        # 根据按键选择模式
        if hasattr(context.controller, 'last_button'):
            if context.controller.last_button == 'BTN1':
                # 选择快速拍照模式
                context.set_data('photo_mode', 'quick')
                context.logger.log_step("拍照模式", "用户选择快速拍照模式")
                context.oled_display.show_text_oled("快速拍照模式\n准备拍照...")
            elif context.controller.last_button == 'BTN2':
                # 选择拍照+语音模式
                context.set_data('photo_mode', 'voice')
                context.logger.log_step("拍照模式", "用户选择拍照+语音模式")
                context.oled_display.show_text_oled("拍照+语音模式\n15秒倒计时拍照")
        else:
            # 默认选择快速拍照
            context.set_data('photo_mode', 'quick')
            context.logger.log_step("拍照模式", "默认选择快速拍照模式")
        
        context.sleep(2)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：根据选择的模式决定"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        # 根据用户选择的拍照模式决定下一个状态
        photo_mode = context.get_data('photo_mode', 'quick')
        
        if photo_mode == 'voice':
            return DeriveState.TAKE_PHOTO_WITH_VOICE
        else:
            return DeriveState.TAKE_PHOTO 