from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState

class ShowFeedbackState(AbstractState):
    """显示反馈状态"""
    
    def __init__(self):
        super().__init__(DeriveState.SHOW_FEEDBACK)
    
    def execute(self, context) -> None:
        """执行显示反馈逻辑"""
        try:
            # 获取反馈内容
            feedback_text = context.get_data('feedback_text', '谢谢你的陪伴和探索！')
            slime_tone = context.get_slime_attribute('tone')
            
            context.logger.log_step("显示反馈", "展示史莱姆反馈")
            
            # 显示反馈标题
            context.oled_display.show_text_oled("史莱姆的感受：")
            context.sleep(2)
            
            # 显示反馈内容
            context.oled_display.wait_for_button_with_text(
                context.controller,
                f"史莱姆说：\n{feedback_text}"
            )
            
            # 显示结束提示
            context.oled_display.wait_for_button_with_text(
                context.controller,
                "本次漂流结束\n感谢体验！"
            )
            
        except Exception as e:
            context.logger.log_step("错误", f"显示反馈失败: {str(e)}")
            
            # 显示默认反馈
            context.oled_display.wait_for_button_with_text(
                context.controller,
                "史莱姆说：\n谢谢你的陪伴！\n\n本次漂流结束"
            )
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：询问是否继续"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        # 反馈显示完成，询问是否继续
        return DeriveState.ASK_CONTINUE 