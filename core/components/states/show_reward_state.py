from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState

class ShowRewardState(AbstractState):
    """显示奖励状态"""
    
    def __init__(self):
        super().__init__(DeriveState.SHOW_REWARD)
    
    def execute(self, context) -> None:
        """执行显示奖励逻辑"""
        try:
            # 获取奖励信息
            reward_description = context.get_data('reward_description', '一个特别的奖励')
            reward_reason = context.get_data('reward_reason', '感谢你的探索')
            reward_image_path = context.get_data('reward_image_path')
            reward_level = context.get_data('reward_level', 'encouragement')
            
            context.logger.log_step("显示奖励", f"展示 {reward_level} 级奖励")
            
            # 根据奖励等级添加不同的祝贺词
            congratulations = {
                'great': '太棒了！',
                'encouragement': '继续加油！'
            }
            
            congrats_text = congratulations.get(reward_level, '很好！')
            
            # 显示奖励图片（如果有的话）
            if reward_image_path:
                try:
                    # 先在LCD上显示奖励图片
                    from PIL import Image
                    img = Image.open(reward_image_path)
                    context.lcd_display.show_image(img)
                    context.logger.log_step("显示奖励", f"奖励图片已显示: {reward_image_path}")
                    
                    # 在OLED上显示祝贺文字
                    context.oled_display.show_text_oled(f"{congrats_text}\n获得奖励！")
                    context.sleep(2)
                    
                except Exception as e:
                    context.logger.log_step("错误", f"显示奖励图片失败: {str(e)}")
                    # 如果图片显示失败，只显示文字
                    self._show_text_reward(context, congrats_text, reward_description, reward_reason)
            else:
                # 没有图片，只显示文字
                self._show_text_reward(context, congrats_text, reward_description, reward_reason)
            
            # 等待用户确认
            context.oled_display.wait_for_button_with_text(
                context.controller,
                f"这是你的奖励：\n{reward_description}"
            )
            
            # 显示奖励原因
            context.oled_display.wait_for_button_with_text(
                context.controller,
                f"史莱姆说：\n{reward_reason}"
            )
            
        except Exception as e:
            context.logger.log_step("错误", f"显示奖励失败: {str(e)}")
            
            # 显示默认奖励信息
            context.oled_display.wait_for_button_with_text(
                context.controller,
                "史莱姆给了你\n一个特别的奖励！"
            )
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：反馈生成"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        return DeriveState.GENERATE_FEEDBACK
    
    def _show_text_reward(self, context, congrats_text, reward_description, reward_reason):
        """显示纯文本奖励"""
        # 分步显示奖励信息
        context.oled_display.show_text_oled(f"{congrats_text}\n\n获得奖励！")
        context.sleep(2)
        
        # 显示奖励描述
        context.oled_display.show_text_oled(f"奖励内容：\n{reward_description[:60]}...")
        context.sleep(3) 