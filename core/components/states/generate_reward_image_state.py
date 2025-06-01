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
                A complete 1-bit pixel art scene featuring a magical accessory or item that perfectly matches a slime's fantasy quirk.
                
                Slime's quirk/fantasy: "{quirk}"
                Reward description: "{reward_description}"
                
                SCENE COMPOSITION:
                - Create a magical environment where this special reward item belongs
                - Show the item in its natural magical setting or workshop
                - Include background elements that enhance the item's significance
                - Create a scene that tells the story of how special this reward is
                - Environment should reflect the magical nature of the quirk fulfillment
                
                REWARD ITEM DESIGN:
                - An accessory, decoration, or special item that would fulfill this slime's fantasy quirk
                - It should be an item the slime can wear, use, or display
                - The item should directly relate to their quirk: "{quirk}"
                - The item should look magical and special
                - Simple but recognizable design suitable for 1-bit graphics
                - The item should look like it could make the slime's dreams come true
                
                BACKGROUND ELEMENTS (all in 1-bit pixel art):
                - Magical workshop, treasure chamber, or mystical environment
                - Shelves, pedestals, or display areas with pixel patterns
                - Magical symbols or runes using simple black pixel designs
                - Tools, books, or artifacts related to the quirk in the background
                - Environmental storytelling through pixel placement
                - Simple architectural elements that suggest a special place
                
                Examples based on quirk:
                - If quirk involves collecting, show a treasure room with display cases and shelves
                - If quirk involves creating, show a magical workshop with tools and materials
                - If quirk involves exploring, show a map room with compass and navigation tools
                - If quirk involves music, show a concert hall or music studio setting
                
                STRICT 1-bit monochrome pixel art requirements:
                - ONLY BLACK AND WHITE (1-bit color depth)
                - Pure monochrome like classic Game Boy or early computer graphics
                - Visible pixel grid structure with chunky square pixels
                - Hard edges with NO anti-aliasing or smoothing
                - NO grayscale, NO color, ONLY pure black and pure white
                - Blocky, pixelated appearance like classic handheld RPG item scenes
                - NO cartoon, anime, or smooth vector art styles
                - Sharp, geometric pixel boundaries
                - Reminiscent of original Game Boy RPG treasure rooms (early Final Fantasy Legend style)
                - Each pixel should be clearly visible as black or white squares
                - NO gradients, NO dithering, only solid black and solid white areas
                - High contrast monochrome aesthetic
                - Scene should look like a reward screen from a 1-bit handheld game
                
                ENVIRONMENTAL DETAILS:
                - Simple geometric background objects using black pixel outlines
                - Textured surfaces using black pixel patterns
                - Simple repeating patterns for walls, floors, or magical effects
                - Objects that enhance the reward's significance and story
                - Magical atmosphere through pixel art environmental design
                
                Style: 1-bit pixel art, monochrome, black and white, classic Game Boy RPG treasure room/reward chamber with detailed magical environment
                """
            else:
                # encouragement级别：符合偏执反应的史莱姆蛋
                reward_prompt = f"""
                A complete 1-bit pixel art scene featuring a special slime egg that embodies the slime's quirky reaction pattern.
                
                Slime's reflex/reaction: "{reflex}"
                Reward description: "{reward_description}"
                
                SCENE COMPOSITION:
                - Create a nurturing environment where this special egg is being cared for
                - Show the egg in a natural or magical incubation setting
                - Include background elements that suggest growth and potential
                - Create a scene that tells the story of new life and encouragement
                - Environment should reflect hope and the promise of new adventures
                
                EGG DESIGN:
                - A unique slime egg that reflects this reaction pattern
                - The egg should visually represent the reflex: "{reflex}"
                - Black pixel patterns on white egg that hint at this behavioral trait
                - The egg should look mysterious but encouraging
                - Simple geometric patterns suitable for 1-bit graphics
                - A sense that this egg contains a slime with similar interesting quirks
                
                BACKGROUND ELEMENTS (all in 1-bit pixel art):
                - Nurturing environment like a cozy cave, garden, or incubation chamber
                - Natural elements like grass, rocks, or simple plant life
                - Soft bedding or nest materials using pixel patterns
                - Other environmental hints about slime care and growth
                - Simple architectural or natural elements that suggest safety
                - Warm, welcoming atmosphere through pixel art design
                
                Examples based on reflex:
                - If reflex involves curiosity, show an egg in a library or study with books and scrolls
                - If reflex involves collecting, show an egg in a treasure chamber with gentle lighting
                - If reflex involves exploring, show an egg in a map room or navigation chamber
                - If reflex involves being cautious, show an egg in a protected, cozy sanctuary
                
                STRICT 1-bit monochrome pixel art requirements:
                - ONLY BLACK AND WHITE (1-bit color depth)
                - Pure monochrome like classic Game Boy or early computer graphics
                - Visible pixel grid structure with chunky square pixels
                - Hard edges with NO anti-aliasing or smoothing
                - NO grayscale, NO color, ONLY pure black and pure white
                - Blocky, pixelated egg with chunky black pixel patterns on white
                - NO cartoon, anime, or smooth vector art styles
                - Sharp, geometric pixel boundaries
                - Reminiscent of classic handheld game egg incubation scenes
                - Each pixel should be clearly visible as black or white squares
                - NO gradients, NO dithering, only solid black and solid white areas
                - High contrast monochrome aesthetic
                - Scene should look like it came from a retro 1-bit life simulation game
                
                ENVIRONMENTAL DETAILS:
                - Simple geometric background objects using black pixel outlines
                - Textured surfaces using black pixel patterns for nesting materials
                - Simple repeating patterns for ground, walls, or natural elements
                - Environmental storytelling through careful pixel placement
                - Objects that enhance the sense of care and growth potential
                
                Style: 1-bit pixel art, monochrome, black and white, classic Game Boy egg incubation/care scene with nurturing environment
                The scene should look hopeful and promising, showing the egg in a caring environment
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