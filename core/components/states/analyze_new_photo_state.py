import base64
from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils, encode_image

class AnalyzeNewPhotoState(AbstractState):
    """分析新照片状态 - 结合照片和语音信息"""
    
    def __init__(self):
        super().__init__(DeriveState.ANALYZE_NEW_PHOTO)
    
    def execute(self, context) -> None:
        """执行分析新照片+语音逻辑"""
        context.oled_display.show_text_oled("史莱姆正在\n观察照片和\n听取描述...")
        
        try:
            new_photo_path = context.get_data('new_timestamped_image')
            if not new_photo_path:
                raise ValueError("没有找到新照片路径")
            
            # 获取语音文本（如果有）
            voice_text = context.get_data('new_photo_voice_text', '')
            
            # 编码图片为base64
            base64_image = encode_image(new_photo_path)
            data_url = f"data:image/jpeg;base64,{base64_image}"
            
            context.logger.log_step("分析新照片+语音", f"开始分析新照片: {new_photo_path}, 语音长度: {len(voice_text)}")
            
            # 获取史莱姆的执念和属性
            slime_obsession = context.get_slime_attribute('obsession')
            slime_tone = context.get_slime_attribute('tone')
            
            # 使用聊天工具分析照片和语音
            chat_utils = DeriveChatUtils(context.response_id)
            
            # 构建综合分析提示
            if voice_text and len(voice_text.strip()) > 0:
                analysis_text = f"""
                请仔细观察这张新照片，并结合用户的语音描述，判断它是否符合史莱姆的执念。
                
                史莱姆的执念: {slime_obsession}
                史莱姆的语气: {slime_tone}
                
                用户的语音描述: "{voice_text}"
                
                请从史莱姆的视角综合分析:
                1. 这张照片中的内容是什么？
                2. 用户的语音描述提供了什么额外信息？
                3. 照片内容和语音描述是否与我的执念相符？
                4. 符合程度如何（完全符合/部分符合/不符合）？
                5. 为什么这么判断？
                
                请用{slime_tone}的语气回答，优先考虑用户的描述感受，控制在150字以内。
                """
            else:
                analysis_text = f"""
                请仔细观察这张新照片，判断它是否符合史莱姆的执念。
                
                史莱姆的执念: {slime_obsession}
                史莱姆的语气: {slime_tone}
                
                请从史莱姆的视角分析:
                1. 这张照片中的内容是什么？
                2. 这些内容是否与我的执念相符？
                3. 符合程度如何（完全符合/部分符合/不符合）？
                4. 为什么这么判断？
                
                请用{slime_tone}的语气回答，控制在150字以内。
                """
            
            # 构建包含图片和文本的输入
            input_content = [
                {"type": "input_text", "text": analysis_text},
                {"type": "input_image", "image_url": data_url}
            ]
            
            response = chat_utils.chat_with_continuity(input_content)
            context.response_id = chat_utils.response_id
            
            # 保存新照片分析结果
            context.set_data('new_photo_analysis', response)
            
            # 记录分析结果
            analysis_type = "照片+语音分析" if voice_text else "照片分析"
            context.logger.log_step(f"分析新{analysis_type}", f"分析完成: {response[:50]}...")
            
            # 显示分析结果，包含语音信息
            if voice_text and len(voice_text.strip()) > 0:
                display_text = f"史莱姆听了你的话\n看了照片后说：\n{response[:60]}..."
            else:
                display_text = f"史莱姆看了看：\n{response[:80]}..."
                
            result = context.oled_display.wait_for_button_with_text(
                context.controller,
                display_text,
                context=context
            )
            
            # 检查是否是长按返回菜单
            if result == 2:
                context.logger.log_step("用户操作", "用户长按按钮2返回菜单")
                return
            
        except Exception as e:
            context.logger.log_step("错误", f"分析新照片+语音失败: {str(e)}")
            
            # 设置默认分析结果
            voice_text = context.get_data('new_photo_voice_text', '')
            if voice_text:
                default_analysis = f"听了你的描述，看起来很有意思！让我想想这能带来什么奖励..."
            else:
                default_analysis = "看起来很有趣，让我想想这能带来什么奖励..."
                
            context.set_data('new_photo_analysis', default_analysis)
            
            # 显示默认分析结果
            result = context.oled_display.wait_for_button_with_text(
                context.controller,
                f"史莱姆看了看：\n{default_analysis}",
                context=context
            )
            
            # 检查是否是长按返回菜单
            if result == 2:
                context.logger.log_step("用户操作", "用户长按按钮2返回菜单")
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        return DeriveState.ANALYZE_REWARD 