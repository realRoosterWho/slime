from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState

class WaitForNewPhotoState(AbstractState):
    """等待新照片状态"""
    
    def __init__(self):
        super().__init__(DeriveState.WAIT_FOR_NEW_PHOTO)
    
    def execute(self, context) -> None:
        """执行等待新照片逻辑"""
        context.logger.log_step("等待新照片", "提示用户准备拍摄新照片")
        
        # 显示提示信息
        prompt_text = f"现在去{context.get_data('destination_suggestion', '探索吧')}\n\n找到目标后\n按钮1拍照"
        
        # 等待用户按钮1拍照
        context.oled_display.wait_for_button_with_text(
            context.controller,
            prompt_text,
            context=context
        )
        
        # 记录用户操作
        context.logger.log_step("用户操作", "用户准备拍摄新照片")
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        return DeriveState.TAKE_NEW_PHOTO 