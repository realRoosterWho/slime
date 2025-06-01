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
        
        # 构建自然语言风格的史莱姆场景提示词，符合Flux最佳实践
        prompt = f"""
        Create a charming 1-bit pixel art scene featuring a slime character with these specific traits: {slime_description}
        
        The slime should be the main character in this scene, clearly displaying its personality through its expression and pose. Design the slime as a simple blob shape with large square eyes and a tiny mouth, but make sure its unique characteristics from the description really shine through.
        
        Place this slime in a simple environment that matches its personality and tells its story. The background should complement the slime's character without overwhelming it - perhaps a cozy cave if it's shy, a garden if it loves nature, or a workshop if it's creative.
        
        Render everything in classic Game Boy style monochrome pixel art. Use only pure black and white pixels with no gray tones. The pixels should look chunky and clearly defined, just like the original handheld games from the 1980s. Focus on high contrast and clean, sharp edges.
        
        Make this scene feel warm and inviting, showing the slime living its best life in its perfect little world.
        """
        
        return prompt 