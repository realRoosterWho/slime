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
                Create a magical 1-bit pixel art scene showcasing a special reward item for a slime whose greatest quirk is: {quirk}
                
                This reward should be a magical item that perfectly fulfills the slime's deepest fantasy. Design something that would make this slime's heart sing with joy - whether it's a beautiful collection display, magical crafting tools, an enchanted compass for exploration, or whatever fits their unique personality.
                
                Show this precious item in a magical setting that tells its story. Perhaps place it on an ornate pedestal in a treasure chamber, or display it in a cozy workshop surrounded by related magical tools. The environment should make the reward feel truly special and significant.
                
                Render everything in classic Game Boy style monochrome pixel art using only pure black and white pixels. Make the magical item the clear focal point, but let the environment enhance its importance and tell the story of why this reward is so perfect for this particular slime.
                
                The reward description mentions: {reward_description}
                """
            else:
                # encouragement级别：符合偏执反应的史莱姆蛋
                reward_prompt = f"""
                Create a heartwarming 1-bit pixel art scene featuring a special slime egg that embodies this unique reaction pattern: {reflex}
                
                This egg should look promising and full of potential, with gentle patterns on its shell that hint at the wonderful personality trait it contains. Design the egg so that someone looking at it would think "I wonder what amazing little slime is growing in there!"
                
                Place this special egg in a nurturing environment that suggests care and growth. Maybe show it resting in a cozy nest, sitting safely in a warm cave, or being tended in a magical incubation chamber. The setting should feel safe, encouraging, and full of hope for the future.
                
                Render everything in classic Game Boy style monochrome pixel art using only pure black and white pixels. Make the egg feel like a precious gift that holds great promise, surrounded by an environment that speaks of patience, care, and anticipation.
                
                The reward description mentions: {reward_description}
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