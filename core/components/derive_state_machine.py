from .abstract_state_machine import AbstractStateMachine
from .derive_states import DeriveState
from .derive_context import DeriveContext
from .states import InitState, GenSlimeImageState, ShowSlimeImageState

class DeriveStateMachine(AbstractStateMachine):
    """史莱姆漂流状态机实现"""
    
    def __init__(self, initial_text: str):
        """初始化状态机
        
        Args:
            initial_text: 用户输入的初始文本
        """
        context = DeriveContext(initial_text)
        super().__init__(context)
    
    def initialize_states(self) -> None:
        """初始化所有状态"""
        # 目前只注册已实现的三个状态
        self.register_state(InitState())
        self.register_state(GenSlimeImageState())
        self.register_state(ShowSlimeImageState())
        
        print("✅ 状态机初始化完成，已注册 3 个状态")
    
    def get_initial_state(self) -> DeriveState:
        """获取初始状态"""
        return DeriveState.INIT

def main():
    """测试函数"""
    initial_text = "感觉空气布满了水雾，有一种看不清前方道路的错觉，觉得很放松。你能带我在这个氛围里面漂流吗？"
    
    # 创建并运行状态机
    state_machine = DeriveStateMachine(initial_text)
    return_to_menu = state_machine.run()
    
    if return_to_menu:
        print("正常返回菜单系统")
        return 42  # 特殊退出码表示返回菜单
    else:
        print("正常结束程序")
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 