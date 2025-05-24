from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState

class AskContinueState(AbstractState):
    """询问是否继续状态"""
    
    def __init__(self):
        super().__init__(DeriveState.ASK_CONTINUE)
    
    def execute(self, context) -> None:
        """执行询问是否继续逻辑"""
        context.logger.log_step("询问继续", "询问用户是否继续漂流")
        
        # 显示询问信息
        question = "想要继续漂流吗？"
        
        # 使用DisplayManager的继续询问功能，传入context用于长按检测
        continue_choice = context.oled_display.show_continue_drift_option(
            context.controller,
            question,
            context  # 传入context用于长按检测
        )
        
        # 检查是否是长按返回菜单
        if continue_choice == 2:
            context.logger.log_step("用户操作", "用户长按按钮2返回菜单")
            return
        
        # 检查是否要返回菜单
        if context.should_return_to_menu():
            context.logger.log_step("用户操作", "用户选择返回菜单")
            return
        
        # 保存用户选择
        context.set_data('continue_derive', continue_choice)
        
        if continue_choice:
            context.logger.log_step("用户选择", "用户选择继续漂流")
            # 增加循环计数
            cycle_count = context.get_data('cycle_count', 0) + 1
            context.set_data('cycle_count', cycle_count)
            context.logger.log_step("循环计数", f"第{cycle_count}轮漂流")
        else:
            context.logger.log_step("用户选择", "用户选择结束漂流")
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        continue_choice = context.get_data('continue_derive', False)
        
        if continue_choice:
            # 继续漂流，回到等待新照片状态
            return DeriveState.WAIT_FOR_NEW_PHOTO
        else:
            # 结束漂流，进入总结状态
            return DeriveState.SUMMARY 