from abc import ABC, abstractmethod
from typing import Dict, Optional
import sys
import signal
import time

from .abstract_state import AbstractState
from .derive_states import DeriveState
from .derive_context import DeriveContext

class AbstractStateMachine(ABC):
    """抽象状态机基类，定义状态机的基本行为 - 优化版本"""
    
    def __init__(self, context: DeriveContext):
        self.context = context
        self.current_state: Optional[AbstractState] = None
        self.states: Dict[DeriveState, AbstractState] = {}
        self.is_running = False
        self.transition_count = 0  # 状态转换计数
        self.error_recovery_attempts = 0  # 错误恢复尝试次数
        self.max_error_recovery = 3  # 最大错误恢复次数
        
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
        print(f"📋 注册状态: {state.state_type.name}")
    
    def validate_states(self) -> bool:
        """验证所有状态是否正确注册"""
        try:
            initial_state = self.get_initial_state()
            if initial_state not in self.states:
                print(f"❌ 初始状态 {initial_state.name} 未注册")
                return False
            
            # 检查状态之间的连接完整性
            unconnected_states = []
            for state_type, state in self.states.items():
                # 创建临时context来测试get_next_state
                try:
                    next_state = state.get_next_state(self.context)
                    if next_state and next_state not in [DeriveState.EXIT] and next_state not in self.states:
                        unconnected_states.append((state_type, next_state))
                except Exception:
                    # get_next_state可能依赖运行时数据，跳过验证
                    pass
            
            if unconnected_states:
                print(f"⚠️  发现未连接的状态转换: {unconnected_states}")
                # 不阻止运行，只是警告
            
            print(f"✅ 状态验证完成，共 {len(self.states)} 个状态")
            return True
            
        except Exception as e:
            print(f"❌ 状态验证失败: {e}")
            return False
    
    def transition_to(self, state_type: DeriveState) -> bool:
        """转换到指定状态 - 增强版本"""
        try:
            if state_type not in self.states:
                print(f"❌ 状态 {state_type.name} 未注册")
                return False
            
            # 检查是否需要返回菜单
            if self.context.should_return_to_menu():
                print("🔄 检测到返回菜单请求，停止状态转换")
                return False
            
            # 退出当前状态
            if self.current_state:
                try:
                    self.current_state.exit(self.context)
                except Exception as e:
                    print(f"⚠️  退出状态 {self.current_state} 时出错: {e}")
            
            # 切换到新状态
            new_state = self.states[state_type]
            old_state_name = self.current_state.state_type.name if self.current_state else "None"
            
            print(f"\n🔄 状态转换 #{self.transition_count + 1}: {old_state_name} → {new_state.state_type.name}")
            
            self.current_state = new_state
            self.transition_count += 1
            
            # 进入新状态
            try:
                self.current_state.enter(self.context)
                return True
            except Exception as e:
                print(f"❌ 进入状态 {new_state} 时出错: {e}")
                return False
                
        except Exception as e:
            print(f"❌ 状态转换失败: {e}")
            return False
    
    def run(self) -> bool:
        """运行状态机 - 优化版本
        
        Returns:
            bool: True表示需要返回菜单，False表示正常退出
        """
        try:
            # 验证上下文状态
            if not self.context.validate_state():
                print("❌ 上下文状态验证失败，无法启动状态机")
                return False
            
            # 初始化状态
            print("🚀 初始化状态机...")
            self.initialize_states()
            
            # 验证状态
            if not self.validate_states():
                print("❌ 状态验证失败，无法启动状态机")
                return False
            
            # 转换到初始状态
            initial_state = self.get_initial_state()
            if not self.transition_to(initial_state):
                print("❌ 无法转换到初始状态")
                return False
            
            self.is_running = True
            print(f"✅ 状态机启动成功，开始执行...")
            
            # 记录开始时间
            start_time = time.time()
            
            while self.is_running and self.current_state:
                try:
                    # 检查返回菜单状态
                    if self.context.should_return_to_menu():
                        print("🔄 检测到返回菜单状态")
                        break
                    
                    # 执行当前状态
                    print(f"\n🎯 执行状态: {self.current_state.state_type.name}")
                    execution_start = time.time()
                    
                    self.current_state.execute(self.context)
                    
                    execution_time = time.time() - execution_start
                    print(f"⏱️  状态执行耗时: {execution_time:.2f}秒")
                    
                    # 重置错误恢复计数（成功执行状态）
                    self.error_recovery_attempts = 0
                    
                    # 再次检查返回菜单（状态执行后）
                    if self.context.should_return_to_menu():
                        print("🔄 状态执行后检测到返回菜单状态")
                        break
                    
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
                        if not self.transition_to(next_state_type):
                            print("❌ 状态转换失败，尝试错误恢复")
                            if not self._attempt_error_recovery():
                                break
                
                except Exception as e:
                    if not self._handle_state_error(e):
                        break
            
            # 记录运行统计
            total_time = time.time() - start_time
            print(f"\n📊 状态机运行统计:")
            print(f"   总运行时间: {total_time:.2f}秒")
            print(f"   状态转换次数: {self.transition_count}")
            print(f"   错误恢复次数: {self.error_recovery_attempts}")
            
            # 记录性能统计
            self.context.log_performance_stats()
        
        except Exception as e:
            self._handle_fatal_error(e)
        
        finally:
            self.is_running = False
            self._cleanup()
        
        return self.context.return_to_menu
    
    def stop(self) -> None:
        """停止状态机"""
        print("🛑 状态机停止请求")
        self.is_running = False
    
    def _attempt_error_recovery(self) -> bool:
        """尝试错误恢复"""
        self.error_recovery_attempts += 1
        
        if self.error_recovery_attempts > self.max_error_recovery:
            print(f"❌ 错误恢复尝试次数已达上限 ({self.max_error_recovery})")
            return False
        
        print(f"🔧 尝试错误恢复 #{self.error_recovery_attempts}")
        
        try:
            # 尝试重新验证上下文
            if not self.context.validate_state():
                print("❌ 上下文状态损坏，无法恢复")
                return False
            
            # 尝试转换到安全状态（通常是CLEANUP状态）
            if DeriveState.CLEANUP in self.states:
                print("🔧 转换到清理状态进行恢复")
                return self.transition_to(DeriveState.CLEANUP)
            
            # 如果没有清理状态，尝试退出
            print("🔧 没有清理状态，准备退出")
            return False
            
        except Exception as e:
            print(f"❌ 错误恢复失败: {e}")
            return False
    
    def _handle_state_error(self, error: Exception) -> bool:
        """处理状态执行错误 - 增强版本"""
        error_msg = f"状态 {self.current_state.state_type.name} 执行出错: {str(error)}"
        print(f"\n❌ {error_msg}")
        
        # 记录错误
        if self.context.logger:
            self.context.logger.log_step("状态错误", error_msg)
        
        # 显示错误信息给用户
        try:
            self.context.oled_display.show_text_oled("程序出错\n正在恢复...")
            time.sleep(2)
        except Exception:
            pass
        
        import traceback
        traceback.print_exc()
        
        # 尝试错误恢复
        return self._attempt_error_recovery()
    
    def _handle_fatal_error(self, error: Exception) -> None:
        """处理致命错误 - 增强版本"""
        error_msg = f"状态机运行出错: {str(error)}"
        print(f"\n💥 {error_msg}")
        
        # 记录错误
        if self.context.logger:
            self.context.logger.log_step("致命错误", error_msg)
            # 确保保存错误日志
            try:
                self.context.logger.save_log()
            except Exception:
                pass
        
        # 显示错误信息给用户
        try:
            self.context.oled_display.show_text_oled("程序严重错误\n即将退出...")
            time.sleep(3)
        except Exception:
            pass
        
        import traceback
        traceback.print_exc()
    
    def _cleanup_handler(self, signum, frame):
        """信号处理器：清理资源并优雅退出 - 优化版本"""
        print("\n🛑 检测到中断信号，正在清理资源...")
        
        try:
            if self.context.logger:
                self.context.logger.log_step("中断", "检测到中断信号，程序退出")
                try:
                    self.context.logger.save_log()
                except Exception:
                    pass
            
            self._cleanup()
            print("✅ 已清理资源")
        except Exception as e:
            print(f"清理过程中出错: {e}")
        finally:
            sys.exit(0)
    
    def _cleanup(self) -> None:
        """清理资源 - 优化版本"""
        try:
            print("🧹 开始清理状态机资源...")
            
            # 退出当前状态
            if self.current_state:
                try:
                    self.current_state.exit(self.context)
                    print(f"🧹 已退出状态: {self.current_state.state_type.name}")
                except Exception as e:
                    print(f"退出状态时出错: {e}")
            
            # 清理上下文
            try:
                self.context.cleanup()
                print("🧹 已清理上下文")
            except Exception as e:
                print(f"清理上下文时出错: {e}")
            
            print("✅ 状态机资源清理完成")
            
        except Exception as e:
            print(f"清理过程中出错: {e}") 