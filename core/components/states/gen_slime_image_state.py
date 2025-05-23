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
        
        # 构建复古彩色像素风格的史莱姆提示词
        prompt = f"""
        A cute slime character with the following traits: {slime_description}
        
        Art style requirements:
        - Retro colorful pixel art style
        - 16-bit or 32-bit game character aesthetic  
        - Vibrant, saturated colors with limited color palette
        - Clean pixel edges with no anti-aliasing
        - Simple but expressive design
        - Large eyes and small mouth for kawaii appeal
        - Soft, rounded blob-like body shape
        - Clear, simple silhouette suitable for game character
        
        The slime should be:
        - Centered in frame
        - Clean background or simple pattern
        - Bright and cheerful appearance
        - Easily recognizable as a friendly slime character
        
        Style: retro pixel art, colorful, game character, nostalgic 16-bit aesthetic
        """
        
        return prompt 