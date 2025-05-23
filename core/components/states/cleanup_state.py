from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState

class CleanupState(AbstractState):
    """清理状态"""
    
    def __init__(self):
        super().__init__(DeriveState.CLEANUP)
    
    def execute(self, context) -> None:
        """执行清理逻辑"""
        context.logger.log_step("开始清理", "史莱姆漂流即将结束")
        
        try:
            # 显示清理信息
            context.oled_display.show_text_oled("正在保存\n漂流记录...")
            
            # 保存最终日志
            context.logger.log_step("漂流完成", "史莱姆漂流体验结束")
            
            # 收集并记录统计信息
            cycle_count = context.get_data('cycle_count', 1)
            all_rewards = context.get_data('all_rewards', [])
            summary = context.get_data('summary', '完成了愉快的漂流')
            
            # 记录统计信息
            context.logger.log_step("统计信息", f"总轮数: {cycle_count}, 总奖励: {len(all_rewards)}个")
            context.logger.log_step("总结", summary)
            
            # 保存日志文件
            context.logger.save_log()
            context.logger.log_step("日志保存", "漂流日志已保存")
            
            # 显示保存成功
            context.oled_display.show_text_oled("记录已保存！\n再见~")
            context.sleep(2)
            
            # 最终清理显示
            context.oled_display.show_text_oled("史莱姆漂流\n体验结束\n\n感谢游玩！")
            context.sleep(3)
            
        except Exception as e:
            context.logger.log_step("清理错误", f"清理过程出错: {str(e)}")
            context.oled_display.show_text_oled("清理完成\n程序结束")
            context.sleep(2)
        
        finally:
            # 执行最终的资源清理
            try:
                context.cleanup()
                context.logger.log_step("资源清理", "所有资源已清理")
            except Exception as e:
                print(f"清理过程中出错: {e}")
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：退出"""
        # 清理完成，正常退出
        return DeriveState.EXIT 