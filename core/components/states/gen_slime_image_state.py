from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveImageUtils

class GenSlimeImageState(AbstractState):
    """生成史莱姆图片状态"""
    
    def __init__(self):
        super().__init__(DeriveState.GEN_SLIME_IMAGE)
        self.image_utils = DeriveImageUtils()
    
    def execute(self, context) -> None:
        """执行生成史莱姆图片逻辑"""
        context.oled_display.show_text_oled("正在生成\n史莱姆形象...")
        
        # 生成史莱姆的图片提示词
        slime_prompt = self._generate_slime_prompt(context)
        context.logger.log_prompt("slime_image_prompt", slime_prompt)
        
        # 使用图像工具生成图片（带重试机制）
        for attempt in range(2):  # 最多重试2次
            try:
                if attempt > 0:
                    context.oled_display.show_text_oled(f"重试生成\n史莱姆图片...")
                
                image_path = self.image_utils.generate_image(
                    slime_prompt, 
                    'slime_image', 
                    'slime', 
                    context
                )
                
                if image_path:
                    context.set_data('slime_image', image_path)
                    context.logger.log_step("生成史莱姆图片", f"史莱姆图片已生成: {image_path}")
                    return
                else:
                    if attempt < 1:
                        context.logger.log_step("生成史莱姆图片", "史莱姆图片生成失败，准备重试")
                    else:
                        raise Exception("史莱姆图片生成重试失败")
            except Exception as e:
                if attempt < 1:
                    context.logger.log_step("错误", f"史莱姆图片生成出错: {str(e)}，准备重试")
                else:
                    context.logger.log_step("错误", f"史莱姆图片生成重试失败: {str(e)}")
                    context.oled_display.show_text_oled("生成史莱姆图片失败\n请稍后再试")
                    raise
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：显示史莱姆图片"""
        return DeriveState.SHOW_SLIME_IMAGE
    
    def _generate_slime_prompt(self, context) -> str:
        """生成史莱姆图片的提示词"""
        slime_description = context.get_data('slime_description', '')
        
        # 构建1-bit黑白像素风格的史莱姆场景提示词
        prompt = f"""
        A complete 1-bit pixel art scene featuring a cute slime character with these traits: {slime_description}
        
        SCENE COMPOSITION:
        - Create a complete environment that matches the slime's personality and traits
        - Include background elements that complement the slime's characteristics
        - Add environmental details that tell a story about this slime
        - Show the slime interacting with or existing in its natural habitat
        - Background should reflect the slime's mood, abilities, or personality
        
        BACKGROUND ELEMENTS (all in 1-bit pixel art):
        - Simple geometric shapes for scenery (trees, rocks, clouds, buildings)
        - Environmental objects that match the slime's story or traits
        - Ground/floor patterns using black pixel textures
        - Sky or ceiling with simple pixel patterns
        - Props or objects that the slime might interact with
        - Simple architectural or natural elements
        - Weather effects using simple black pixel patterns (rain lines, snow dots)
        
        CHARACTER INTEGRATION:
        - Position the slime naturally within the scene
        - Show the slime's relationship to its environment
        - Reflect the slime's personality through its pose and surroundings
        - Make the scene tell a story about who this slime is
        
        STRICT 1-bit monochrome pixel art requirements:
        - ONLY BLACK AND WHITE (1-bit color depth)
        - Pure monochrome like classic Game Boy or early computer graphics
        - Visible pixel grid structure with chunky square pixels
        - Hard edges with NO anti-aliasing or smoothing
        - NO grayscale, NO color, ONLY pure black and pure white
        - Blocky, pixelated appearance like classic 1980s handheld games
        - NO cartoon, anime, or smooth vector art styles
        - Sharp, geometric pixel boundaries
        - Reminiscent of original Game Boy or Apple II graphics
        - Each pixel should be clearly visible as black or white squares
        - NO gradients, NO dithering, only solid black and solid white areas
        - High contrast monochrome aesthetic
        
        CHARACTER DESIGN:
        - Simple geometric blob shape made of black pixels
        - Large square/rectangular eyes (solid black pixels)
        - Tiny pixel mouth (black pixels)
        - Body outline in thick black pixels
        - Interior can be white or have simple black pixel patterns
        - Expression and pose that matches the personality described
        - Clear silhouette suitable for 1-bit retro gaming
        - Must look like it came from a monochrome handheld game
        
        ENVIRONMENTAL DETAILS:
        - Simple geometric background objects using black pixel outlines
        - Textured surfaces using black pixel patterns
        - Simple repeating patterns for ground, walls, or sky
        - Environmental storytelling through pixel placement
        - Objects that enhance the slime's character story
        
        TECHNICAL SPECIFICATIONS:
        - 1-bit pixel art, monochrome, black and white only
        - Complete scene composition with foreground and background
        - High contrast for maximum clarity on monochrome displays
        - NO modern digital art techniques
        - Must look like original Game Boy game screenshots
        - Think classic platformer games, RPGs, or adventure games
        - Detailed but simple environment that tells a story
        
        Style: 1-bit pixel art, monochrome, black and white, classic Game Boy RPG/platformer game screenshot with detailed environment and storytelling
        """
        
        return prompt 