from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveImageUtils

class GenerateRewardImageState(AbstractState):
    """生成奖励图片状态"""
    
    def __init__(self):
        super().__init__(DeriveState.GENERATE_REWARD_IMAGE)
    
    def execute(self, context) -> None:
        """执行生成奖励图片逻辑"""
        context.oled_display.show_text_oled("史莱姆正在\n准备奖励...")
        
        try:
            # 获取奖励信息
            reward_level = context.get_data('reward_level', 'normal')
            reward_description = context.get_data('reward_description', '一个特别的奖励')
            slime_attributes = context.get_data('slime_attributes', {})
            
            context.logger.log_step("生成奖励图片", f"开始生成 {reward_level} 级奖励图片")
            
            # 根据奖励等级调整图片风格
            style_modifiers = {
                'great': 'magnificent, golden, glowing, magical, spectacular',
                'good': 'beautiful, shimmering, colorful, delightful',
                'normal': 'pleasant, cute, friendly, charming',
                'encouragement': 'warm, encouraging, supportive, gentle'
            }
            
            style = style_modifiers.get(reward_level, 'pleasant, cute')
            
            # 构建奖励图片提示词
            reward_prompt = f"""
            A {style} reward item or scene representing "{reward_description}".
            The reward should match a slime character with these traits:
            - Color: {slime_attributes.get('color', 'blue')}
            - Style: kawaii, anime style, friendly
            - Mood: generous and happy to give rewards
            
            The reward image should be:
            - Visually appealing and {style}
            - Suitable for a game reward
            - Related to the slime's personality
            - High quality, detailed illustration
            
            Style: kawaii anime art, soft lighting, magical atmosphere
            """
            
            # 使用图像工具生成奖励图片
            image_utils = DeriveImageUtils()
            reward_image_path = image_utils.generate_image(
                prompt=reward_prompt,
                save_key='reward_image_path',
                image_type='reward',
                context=context
            )
            
            if reward_image_path:
                context.set_data('reward_image_path', reward_image_path)
                context.logger.log_step("生成奖励图片", f"奖励图片已生成: {reward_image_path}")
                context.oled_display.show_text_oled("奖励准备好了！")
            else:
                raise Exception("图片生成失败")
            
        except Exception as e:
            context.logger.log_step("错误", f"生成奖励图片失败: {str(e)}")
            
            # 使用默认的奖励图片路径
            context.set_data('reward_image_path', None)
            context.oled_display.show_text_oled("奖励准备中...")
        
        context.sleep(1)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        return DeriveState.SHOW_REWARD 