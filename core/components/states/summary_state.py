from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils

class SummaryState(AbstractState):
    """总结状态"""
    
    def __init__(self):
        super().__init__(DeriveState.SUMMARY)
    
    def execute(self, context) -> None:
        """执行总结逻辑"""
        context.oled_display.show_text_oled("正在生成\n漂流总结...")
        
        try:
            # 收集漂流数据
            cycle_count = context.get_data('cycle_count', 1)
            slime_obsession = context.get_slime_attribute('obsession')
            slime_tone = context.get_slime_attribute('tone')
            all_rewards = context.get_data('all_rewards', [])
            
            # 添加当前轮次的奖励到总奖励列表
            current_reward = {
                'level': context.get_data('reward_level', 'encouragement'),
                'description': context.get_data('reward_description', '一个奖励'),
                'cycle': cycle_count
            }
            all_rewards.append(current_reward)
            context.set_data('all_rewards', all_rewards)
            
            context.logger.log_step("生成总结", f"开始生成{cycle_count}轮漂流的总结")
            
            # 使用聊天工具生成总结
            chat_utils = DeriveChatUtils(context.response_id)
            
            summary_prompt = f"""
            作为一个有执念的史莱姆，我和玩家一起完成了{cycle_count}轮漂流探索。
            
            我的执念: {slime_obsession}
            我的语气: {slime_tone}
            总共获得的奖励: {len(all_rewards)}个
            
            奖励详情:
            {self._format_rewards(all_rewards)}
            
            请帮我生成一个漂流总结，包含：
            1. 对整个漂流体验的回顾
            2. 史莱姆的满足感和感悟
            3. 对执念的满足程度评价
            4. 对玩家的感谢和鼓励
            
            请用{slime_tone}的语气，控制在120字以内，要温馨且有纪念意义。
            """
            
            response = chat_utils.chat_with_continuity(
                system_content="你是一个即将结束漂流的史莱姆，要对整个体验进行温馨的总结。",
                prompt=summary_prompt
            )
            context.response_id = chat_utils.response_id
            
            # 保存总结内容
            context.set_data('summary', response)
            context.logger.log_step("生成总结", f"总结已生成: {response[:50]}...")
            
            # 显示总结
            self._show_summary(context, response, cycle_count, len(all_rewards))
            
        except Exception as e:
            context.logger.log_step("错误", f"生成总结失败: {str(e)}")
            
            # 设置默认总结
            cycle_count = context.get_data('cycle_count', 1)
            reward_count = len(context.get_data('all_rewards', [])) + 1
            default_summary = f"这次{cycle_count}轮漂流很棒！我们一起获得了{reward_count}个奖励，谢谢你的陪伴！"
            context.set_data('summary', default_summary)
            
            self._show_summary(context, default_summary, cycle_count, reward_count)
    
    def _format_rewards(self, rewards):
        """格式化奖励列表"""
        if not rewards:
            return "暂无奖励"
        
        formatted = []
        for i, reward in enumerate(rewards, 1):
            level_text = {
                'great': '极佳',
                'encouragement': '鼓励'
            }.get(reward['level'], '普通')
            
            formatted.append(f"第{reward.get('cycle', i)}轮: {level_text}级 - {reward['description']}")
        
        return '\n'.join(formatted)
    
    def _show_summary(self, context, summary_text, cycle_count, reward_count):
        """显示总结信息"""
        # 显示统计信息
        stats_text = f"漂流完成！\n{cycle_count}轮探索\n{reward_count}个奖励"
        context.oled_display.show_text_oled(stats_text)
        context.sleep(3)
        
        # 显示总结内容
        context.oled_display.wait_for_button_with_text(
            context.controller,
            f"史莱姆的总结：\n{summary_text}"
        )
        
        # 显示结束感谢
        context.oled_display.wait_for_button_with_text(
            context.controller,
            "感谢你的陪伴！\n希望你喜欢\n这次漂流体验"
        )
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：清理"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        return DeriveState.CLEANUP 