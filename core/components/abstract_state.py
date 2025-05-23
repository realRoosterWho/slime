from abc import ABC, abstractmethod
from typing import Optional
from .derive_states import DeriveState

class AbstractState(ABC):
    """抽象状态基类，定义所有状态的通用接口"""
    
    def __init__(self, state_type: DeriveState):
        self.state_type = state_type
        self.name = state_type.name
    
    def enter(self, context) -> None:
        """进入状态时执行的操作（可选重写）"""
        pass
    
    @abstractmethod
    def execute(self, context) -> None:
        """执行状态的主要逻辑（必须重写）"""
        pass
    
    def exit(self, context) -> None:
        """退出状态时执行的操作（可选重写）"""
        pass
    
    @abstractmethod
    def get_next_state(self, context) -> Optional[DeriveState]:
        """确定下一个状态（必须重写）"""
        pass
    
    def can_handle_long_press(self) -> bool:
        """是否可以处理长按返回菜单（可选重写）"""
        return True
    
    def __str__(self):
        return f"{self.__class__.__name__}({self.state_type.name})"
    
    def __repr__(self):
        return self.__str__() 