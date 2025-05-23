from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils

class GenerateFeedbackState(AbstractState):
    """生成反馈状态"""
    
    def __init__(self):
        super().__init__(DeriveState.GENERATE_FEEDBACK)
    
    def execute(self, context) -> None:
        """执行生成反馈逻辑"""
        context.oled_display.show_text_oled("史莱姆在想\n感受...")
        
        try:
            # 获取相关数据
            reward_level = context.get_data('reward_level', 'normal')
            reward_description = context.get_data('reward_description', '一个奖励')
            new_photo_analysis = context.get_data('new_photo_analysis', '')
            slime_tone = context.get_slime_attribute('tone')
            slime_obsession = context.get_slime_attribute('obsession')
            
            # 使用聊天工具生成反馈
            chat_utils = DeriveChatUtils(context.response_id)
            
            feedback_prompt = f"""
            作为一个有执念的史莱姆，我刚刚给了玩家一个{reward_level}级的奖励"{reward_description}"。
            
            我的执念: {slime_obsession}
            我的语气: {slime_tone}
            这次探索的分析: {new_photo_analysis}
            
            请帮我生成一段反馈，表达我对这次探索体验的感受：
            1. 对这次奖励体验的总结
            2. 对未来探索的期待或建议
            3. 体现史莱姆的个性和执念
            
            请用{slime_tone}的语气，控制在80字以内，要有趣且有个性。
            """
            
            response = chat_utils.chat_with_continuity(
                system_content="你是一个有独特个性的史莱姆，会对探索体验给出个性化的反馈。",
                prompt=feedback_prompt
            )
            context.response_id = chat_utils.response_id
            
            # 保存反馈内容
            context.set_data('feedback_text', response)
            context.logger.log_step("生成反馈", f"反馈已生成: {response[:50]}...")
            
            # 显示生成完成
            context.oled_display.show_text_oled("反馈生成完成！")
            context.sleep(1)
            
        except Exception as e:
            context.logger.log_step("错误", f"生成反馈失败: {str(e)}")
            
            # 设置默认反馈
            default_feedback = "这次探索很有趣！希望我们能继续寻找更多符合我执念的东西！"
            context.set_data('feedback_text', default_feedback)
            
            context.oled_display.show_text_oled("反馈准备完成！")
            context.sleep(1)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：显示反馈"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        return DeriveState.SHOW_FEEDBACK 