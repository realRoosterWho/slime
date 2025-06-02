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
                Create a magical 1-bit pixel art reward item that perfectly embodies this slime's unique trait: {quirk}
                
                Design a special magical item that would fulfill this slime's deepest desires. Show it in an environment that highlights its importance and magical nature.
                
                Render everything in classic Game Boy style monochrome pixel art using only pure black and white pixels. Focus on making the reward feel truly special and significant.
                
                The reward is described as: {reward_description}
                """
            else:
                # encouragement级别：符合偏执反应的史莱姆蛋
                reward_prompt = f"""
                Create a heartwarming 1-bit pixel art slime egg that reflects this personality trait: {reflex}
                
                Design an egg with gentle patterns that hint at the wonderful slime growing inside. Place it in a nurturing environment that suggests care and potential.
                
                Render everything in classic Game Boy style monochrome pixel art using only pure black and white pixels. Make the egg feel like a precious gift full of promise.
                
                The egg is described as: {reward_description}
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