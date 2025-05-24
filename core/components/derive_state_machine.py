from .abstract_state_machine import AbstractStateMachine
from .derive_states import DeriveState
from .derive_context import DeriveContext
from .states import (
    InitState, GenSlimeImageState, ShowSlimeImageState,
    ShowGreetingState, AskPhotoState, TakePhotoState,
    AnalyzePhotoState, SuggestDestinationState,
    WaitForNewPhotoState, TakeNewPhotoState, AnalyzeNewPhotoState,
    AnalyzeRewardState, GenerateRewardImageState, ShowRewardState,
    GenerateFeedbackState, ShowFeedbackState, AskContinueState,
    SummaryState, CleanupState, VoiceInputMoodState, ProcessMoodState
)

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
        # 注册语音输入系统状态 (新增)
        self.register_state(VoiceInputMoodState())
        self.register_state(ProcessMoodState())
        
        # 注册基础流程状态
        self.register_state(InitState())
        self.register_state(GenSlimeImageState())
        self.register_state(ShowSlimeImageState())
        self.register_state(ShowGreetingState())
        self.register_state(AskPhotoState())
        self.register_state(TakePhotoState())
        self.register_state(AnalyzePhotoState())
        self.register_state(SuggestDestinationState())
        
        # 注册奖励系统状态
        self.register_state(WaitForNewPhotoState())
        self.register_state(TakeNewPhotoState())
        self.register_state(AnalyzeNewPhotoState())
        self.register_state(AnalyzeRewardState())
        self.register_state(GenerateRewardImageState())
        self.register_state(ShowRewardState())
        
        # 注册反馈系统状态
        self.register_state(GenerateFeedbackState())
        self.register_state(ShowFeedbackState())
        self.register_state(AskContinueState())
        
        # 注册结束系统状态
        self.register_state(SummaryState())
        self.register_state(CleanupState())
        
        print("✅ 状态机初始化完成，已注册 21 个状态")
        print("📋 语音输入 2 个 + 基础流程 8 个 + 奖励系统 6 个 + 反馈系统 3 个 + 结束系统 2 个状态")
    
    def get_initial_state(self) -> DeriveState:
        """获取初始状态"""
        return DeriveState.VOICE_INPUT_MOOD  # 修改为语音输入状态

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