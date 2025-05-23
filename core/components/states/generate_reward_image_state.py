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
            reward_level = context.get_data('reward_level', 'encouragement')
            reward_description = context.get_data('reward_description', '一个特别的奖励')
            slime_attributes = context.get_data('slime_attributes', {})
            
            # 获取史莱姆的关键属性
            quirk = slime_attributes.get('quirk', '喜欢收集有趣的小物件')
            reflex = slime_attributes.get('reflex', '会好奇地观察新事物')
            obsession = slime_attributes.get('obsession', '寻找美好的事物')
            
            context.logger.log_step("生成奖励图片", f"开始生成 {reward_level} 级奖励图片")
            
            # 根据奖励等级生成不同类型的奖励图片
            if reward_level == 'great':
                # great级别：装扮或符合幻想癖好的物品
                reward_prompt = f"""
                A magical accessory or item that perfectly matches a slime's fantasy quirk.
                
                Slime's quirk/fantasy: "{quirk}"
                Reward description: "{reward_description}"
                
                Generate an accessory, decoration, or special item that would fulfill this slime's fantasy quirk:
                - It should be an item the slime can wear, use, or display
                - The item should directly relate to their quirk: "{quirk}"
                - The item should look magical and special
                - Colors should be vibrant and appealing
                - The item should look like it could make the slime's dreams come true
                
                Examples based on quirk:
                - If quirk involves collecting, show a beautiful collection box or display case
                - If quirk involves creating, show magical crafting tools
                - If quirk involves exploring, show a mystical compass or map
                - If quirk involves music, show a magical instrument
                
                Art style requirements:
                - Retro colorful pixel art style
                - 16-bit or 32-bit game item aesthetic
                - Vibrant, saturated colors with limited color palette
                - Clean pixel edges with no anti-aliasing
                - Simple but recognizable design
                - Game item/equipment appearance
                - Clear, simple silhouette
                
                Style: retro pixel art, colorful, game item, nostalgic 16-bit aesthetic
                Background: simple, clean, focus on the reward item
                """
            else:
                # encouragement级别：符合偏执反应的史莱姆蛋
                reward_prompt = f"""
                A special slime egg that embodies the slime's quirky reaction pattern.
                
                Slime's reflex/reaction: "{reflex}"
                Reward description: "{reward_description}"
                
                Generate a unique slime egg that reflects this reaction pattern:
                - The egg should visually represent the reflex: "{reflex}"
                - Pattern and colors on the egg should hint at this behavioral trait
                - The egg should look mysterious but encouraging
                - Surface patterns, textures, or markings that suggest the reflex behavior
                - A sense that this egg contains a slime with similar interesting quirks
                
                Examples based on reflex:
                - If reflex involves curiosity, show an egg with question mark patterns or swirling designs
                - If reflex involves collecting, show an egg with treasure-like patterns
                - If reflex involves exploring, show an egg with map-like markings or compass designs
                - If reflex involves being cautious, show an egg with protective shell patterns
                
                Art style requirements:
                - Retro colorful pixel art style
                - 16-bit or 32-bit game item aesthetic
                - Vibrant, saturated colors with limited color palette
                - Clean pixel edges with no anti-aliasing
                - Simple but detailed egg design
                - Game collectible item appearance
                - Clear, simple silhouette
                
                Style: retro pixel art, colorful, game collectible, nostalgic 16-bit aesthetic
                Background: simple, clean, focus on the egg
                The egg should look hopeful and promising, not disappointing
                """
            
            context.logger.log_prompt("reward_image_prompt", reward_prompt)
            
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