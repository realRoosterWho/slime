from abc import ABC, abstractmethod
from typing import Dict, Optional
import sys
import signal

from .abstract_state import AbstractState
from .derive_states import DeriveState
from .derive_context import DeriveContext

class AbstractStateMachine(ABC):
    """抽象状态机基类，定义状态机的基本行为"""
    
    def __init__(self, context: DeriveContext):
        self.context = context
        self.current_state: Optional[AbstractState] = None
        self.states: Dict[DeriveState, AbstractState] = {}
        self.is_running = False
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._cleanup_handler)
        signal.signal(signal.SIGTERM, self._cleanup_handler)
    
    @abstractmethod
    def initialize_states(self) -> None:
        """初始化所有状态（子类必须实现）"""
        pass
    
    @abstractmethod
    def get_initial_state(self) -> DeriveState:
        """获取初始状态（子类必须实现）"""
        pass
    
    def register_state(self, state: AbstractState) -> None:
        """注册状态"""
        self.states[state.state_type] = state
    
    def transition_to(self, state_type: DeriveState) -> None:
        """转换到指定状态"""
        if state_type not in self.states:
            raise ValueError(f"状态 {state_type} 未注册")
        
        # 退出当前状态
        if self.current_state:
            self.current_state.exit(self.context)
        
        # 切换到新状态
        new_state = self.states[state_type]
        print(f"\n🔄 状态转换: {self.current_state} -> {new_state}")
        
        self.current_state = new_state
        
        # 进入新状态
        self.current_state.enter(self.context)
    
    def run(self) -> bool:
        """运行状态机
        
        Returns:
            bool: True表示需要返回菜单，False表示正常退出
        """
        try:
            # 初始化状态
            self.initialize_states()
            
            # 转换到初始状态
            initial_state = self.get_initial_state()
            self.transition_to(initial_state)
            
            self.is_running = True
            
            while self.is_running and self.current_state:
                try:
                    # 检查长按返回菜单
                    if (self.current_state.can_handle_long_press() and 
                        self.context.check_btn2_long_press()):
                        print("检测到长按，准备返回菜单")
                        break
                    
                    # 执行当前状态
                    print(f"\n🎯 执行状态: {self.current_state}")
                    self.current_state.execute(self.context)
                    
                    # 获取下一个状态
                    next_state_type = self.current_state.get_next_state(self.context)
                    
                    if next_state_type is None:
                        # 没有下一个状态，退出
                        print("✅ 状态机完成执行")
                        break
                    elif next_state_type == DeriveState.EXIT:
                        # 明确退出
                        print("🚪 状态机请求退出")
                        break
                    else:
                        # 转换到下一个状态
                        self.transition_to(next_state_type)
                
                except Exception as e:
                    self._handle_state_error(e)
                    break
        
        except Exception as e:
            self._handle_fatal_error(e)
        
        finally:
            self.is_running = False
            self._cleanup()
        
        return self.context.return_to_menu
    
    def stop(self) -> None:
        """停止状态机"""
        self.is_running = False
    
    def _handle_state_error(self, error: Exception) -> None:
        """处理状态执行错误"""
        error_msg = f"状态 {self.current_state} 执行出错: {str(error)}"
        print(f"\n❌ {error_msg}")
        
        if self.context.logger:
            self.context.logger.log_step("状态错误", error_msg)
        
        import traceback
        traceback.print_exc()
    
    def _handle_fatal_error(self, error: Exception) -> None:
        """处理致命错误"""
        error_msg = f"状态机运行出错: {str(error)}"
        print(f"\n💥 {error_msg}")
        
        if self.context.logger:
            self.context.logger.log_step("致命错误", error_msg)
            self.context.logger.save_log()
        
        import traceback
        traceback.print_exc()
    
    def _cleanup_handler(self, signum, frame):
        """信号处理器：清理资源并优雅退出"""
        print("\n🛑 检测到中断信号，正在清理资源...")
        
        try:
            if self.context.logger:
                self.context.logger.log_step("中断", "检测到中断信号，程序退出")
                self.context.logger.save_log()
            
            self._cleanup()
            print("✅ 已清理资源")
        except Exception as e:
            print(f"清理过程中出错: {e}")
        finally:
            sys.exit(0)
    
    def _cleanup(self) -> None:
        """清理资源"""
        try:
            # 退出当前状态
            if self.current_state:
                self.current_state.exit(self.context)
            
            # 清理上下文
            self.context.cleanup()
        except Exception as e:
            print(f"清理过程中出错: {e}") 