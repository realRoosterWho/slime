import os
import time
from typing import Optional
from PIL import Image

from ..abstract_state import AbstractState
from ..derive_states import DeriveState

class ShowSlimeImageState(AbstractState):
    """显示史莱姆图片状态"""
    
    def __init__(self):
        super().__init__(DeriveState.SHOW_SLIME_IMAGE)
    
    def execute(self, context) -> None:
        """执行显示史莱姆图片逻辑"""
        slime_image_path = context.get_data('slime_image')
        
        if not slime_image_path or not os.path.exists(slime_image_path):
            context.logger.log_step("显示图片", "跳过图片显示：图片未生成")
            return
            
        try:
            # 显示文本
            context.oled_display.show_text_oled("史莱姆\n绘制完成！")
            time.sleep(1)
            
            # 显示图片
            img = Image.open(slime_image_path)
            context.lcd_display.show_image(img)
            
            context.logger.log_step("显示图片", "史莱姆图片显示成功")
            
            # 等待按钮按下
            self._wait_for_button(context)
            
        except Exception as e:
            context.logger.log_step("错误", f"显示图片时出错: {str(e)}")
            context.oled_display.show_text_oled("图片显示失败...")
            time.sleep(2)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：显示打招呼"""
        return DeriveState.SHOW_GREETING
    
    def _wait_for_button(self, context):
        """等待按钮按下"""
        context.oled_display.wait_for_button_with_text(
            context.controller,
            "按BT1继续"
        ) 