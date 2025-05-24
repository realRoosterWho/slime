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
            
            # 记录奖励到历史记录
            self._record_reward_to_history(context)
            
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
            result = context.oled_display.wait_for_button_with_text(
                context.controller,
                f"这是你的奖励：\n{reward_description}",
                context=context  # 传入context用于长按检测
            )
            
            # 检查是否是长按返回菜单
            if result == 2:
                context.logger.log_step("用户操作", "用户长按按钮2返回菜单")
                return
            
            # 显示奖励原因
            result = context.oled_display.wait_for_button_with_text(
                context.controller,
                f"史莱姆说：\n{reward_reason}",
                context=context  # 传入context用于长按检测
            )
            
            # 检查是否是长按返回菜单
            if result == 2:
                context.logger.log_step("用户操作", "用户长按按钮2返回菜单")
                return
            
        except Exception as e:
            context.logger.log_step("错误", f"显示奖励失败: {str(e)}")
            
            # 显示默认奖励信息
            result = context.oled_display.wait_for_button_with_text(
                context.controller,
                "史莱姆给了你\n一个特别的奖励！",
                context=context  # 传入context用于长按检测
            )
            
            # 检查是否是长按返回菜单
            if result == 2:
                context.logger.log_step("用户操作", "用户长按按钮2返回菜单")
    
    def _record_reward_to_history(self, context):
        """记录奖励到历史记录"""
        try:
            # 获取当前奖励信息
            reward_info = {
                'level': context.get_data('reward_level', 'encouragement'),
                'description': context.get_data('reward_description', '一个特别的奖励'),
                'reason': context.get_data('reward_reason', '感谢你的探索'),
                'image_path': context.get_data('reward_image_path'),
                'cycle': context.get_data('cycle_count', 1),
                'timestamp': context.logger.timestamp
            }
            
            # 获取现有的奖励列表
            all_rewards = context.get_data('all_rewards', [])
            
            # 添加新奖励
            all_rewards.append(reward_info)
            
            # 保存回context
            context.set_data('all_rewards', all_rewards)
            
            # 记录日志
            context.logger.log_step("奖励记录", f"第{len(all_rewards)}个奖励已记录: {reward_info['level']} - {reward_info['description'][:30]}...")
            context.logger.log_step("奖励统计", f"当前获得的奖励总数: {len(all_rewards)}个")
            
        except Exception as e:
            context.logger.log_step("奖励记录错误", f"记录奖励失败: {str(e)}")
    
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