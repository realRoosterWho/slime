from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils

class ShowGreetingState(AbstractState):
    """显示打招呼状态"""
    
    def __init__(self):
        super().__init__(DeriveState.SHOW_GREETING)
    
    def execute(self, context) -> None:
        """执行显示打招呼逻辑"""
        # 使用聊天工具生成打招呼语句
        chat_utils = DeriveChatUtils(context.response_id)
        
        greeting = chat_utils.generate_text('greeting', personality=context.get_data('personality'))
        context.set_data('greeting', greeting)
        context.response_id = chat_utils.response_id
        
        context.logger.log_step("打招呼", greeting)
        
        # 等待按钮按下
        self._wait_for_button(context, f"史莱姆说：\n{greeting}")
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：询问拍照"""
        return DeriveState.ASK_PHOTO
    
    def _wait_for_button(self, context, text):
        """等待按钮按下"""
        context.oled_display.wait_for_button_with_text(
            context.controller,
            text,
            context=context
        ) 