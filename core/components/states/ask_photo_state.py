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
        
        # 直接开始拍照+语音流程
        self._start_photo_voice_process(context)
    
    def _start_photo_voice_process(self, context):
        """开始拍照+语音流程"""
        # 等待用户按钮确认开始拍照+语音
        result = context.oled_display.wait_for_button_with_text(
            context.controller,
            "拍照+语音模式\n\n15秒倒计时摆pose\n同时说出感受\n\nBT1开始",
            context=context
        )
        
        # 检查是否是长按返回菜单
        if result == 2:
            context.logger.log_step("用户操作", "用户长按返回菜单")
            return
        
        # 设置为拍照+语音模式
        context.set_data('photo_mode', 'voice')
        context.logger.log_step("拍照模式", "开始拍照+语音模式")
        
        # 显示准备提示
        context.oled_display.show_text_oled("准备开始\n拍照+语音...")
        context.sleep(2)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：拍照+语音"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        # 直接进入拍照+语音状态
        return DeriveState.TAKE_PHOTO_WITH_VOICE 