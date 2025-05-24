from typing import Optional
import os

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils, encode_image

class ProcessPhotoVoiceState(AbstractState):
    """处理拍照+语音数据状态"""
    
    def __init__(self):
        super().__init__(DeriveState.PROCESS_PHOTO_VOICE)
    
    def execute(self, context) -> None:
        """执行拍照+语音数据处理逻辑"""
        context.logger.log_step("处理拍照+语音", "开始处理拍照时的语音和照片数据")
        
        try:
            # 获取拍照语音和照片数据
            photo_voice_text = context.get_data('photo_voice_text')
            photo_path = context.get_data('timestamped_image')
            
            if not photo_voice_text:
                raise ValueError("没有找到拍照时的语音文本")
            
            context.logger.log_step("数据获取", f"拍照语音文本: {photo_voice_text[:50]}...")
            
            # 检查是否有照片（如果拍照失败可能没有）
            if photo_path and not context.get_data('photo_failed'):
                # 有照片，进行照片+语音组合分析
                self._analyze_photo_with_voice(context, photo_path, photo_voice_text)
            else:
                # 仅分析语音文本
                self._analyze_voice_only(context, photo_voice_text)
            
            context.logger.log_step("处理拍照+语音", "拍照+语音数据处理完成")
            
        except Exception as e:
            context.logger.log_step("错误", f"处理拍照+语音数据失败: {str(e)}")
            # 发生错误时使用默认处理
            self._use_fallback_analysis(context)
    
    def _analyze_photo_with_voice(self, context, photo_path: str, voice_text: str):
        """分析照片+语音组合数据"""
        context.oled_display.show_text_oled("正在分析\n照片和语音...")
        
        try:
            # 添加详细的调试信息
            context.logger.log_step("照片路径检查", f"照片路径: {photo_path}")
            
            # 检查照片文件是否存在
            if not os.path.exists(photo_path):
                raise FileNotFoundError(f"照片文件不存在: {photo_path}")
            
            # 检查文件大小
            file_size = os.path.getsize(photo_path)
            context.logger.log_step("照片文件检查", f"文件大小: {file_size} bytes")
            
            if file_size == 0:
                raise ValueError("照片文件为空")
            
            # 编码照片为base64
            context.logger.log_step("照片编码", "开始Base64编码...")
            base64_image = encode_image(photo_path)
            context.logger.log_step("照片编码完成", f"Base64长度: {len(base64_image)} 字符")
            
            data_url = f"data:image/jpeg;base64,{base64_image}"
            
            # 使用聊天工具进行组合分析
            chat_utils = DeriveChatUtils(context.response_id)
            
            # 构建照片+语音分析提示
            analysis_prompt = f"""
            请结合这张照片和用户在拍照时说的话来进行综合分析。
            
            用户拍照时的语音描述: "{voice_text}"
            
            请从以下角度进行分析:
            1. 照片中展现的视觉内容
            2. 用户语音中表达的主观感受
            3. 视觉与感受的结合点
            4. 这个场景给人的整体印象
            5. 适合什么样的史莱姆角色
            
            请用丰富的描述性语言回答，控制在200字以内。
            """
            
            # 构建输入内容
            input_content = [
                {"type": "input_text", "text": analysis_prompt},
                {"type": "input_image", "image_url": data_url}
            ]
            
            context.logger.log_step("AI分析请求", "发送照片+语音到AI...")
            
            # 调用分析
            combined_analysis = chat_utils.chat_with_continuity(input_content)
            
            # 检查AI是否真的看到了照片
            if "抱歉" in combined_analysis or "无法" in combined_analysis or "看到" not in combined_analysis.lower():
                context.logger.log_step("AI分析警告", "AI可能无法识别照片内容")
                context.logger.log_step("AI回复检查", f"回复内容: {combined_analysis[:100]}...")
                
                # 回退到仅语音分析，但记录照片问题
                context.logger.log_step("处理策略", "AI无法识别照片，回退到语音分析")
                self._analyze_voice_only(context, voice_text)
                return
            
            # 保存分析结果
            context.set_data('photo_description', combined_analysis)
            context.set_data('voice_enhanced_analysis', True)  # 标记为语音增强分析
            context.response_id = chat_utils.response_id
            
            context.logger.log_step("照片+语音分析成功", combined_analysis)
            
        except Exception as e:
            context.logger.log_step("照片+语音分析错误", f"分析失败: {str(e)}")
            # 回退到仅语音分析
            self._analyze_voice_only(context, voice_text)
    
    def _analyze_voice_only(self, context, voice_text: str):
        """仅分析语音文本（当没有照片时）"""
        context.oled_display.show_text_oled("正在分析\n语音描述...")
        
        try:
            # 使用聊天工具分析语音内容
            chat_utils = DeriveChatUtils(context.response_id)
            
            # 构建语音分析提示
            voice_analysis_prompt = f"""
            用户在某个场景中表达了这样的感受和描述: "{voice_text}"
            
            请基于这段话分析:
            1. 用户当时所处的环境可能是什么样的
            2. 用户的心理状态和情感倾向
            3. 这个场景的氛围和特点
            4. 适合生成什么样的史莱姆角色来匹配这种感受
            
            请用生动的描述回答，控制在150字以内。
            """
            
            # 调用分析
            voice_analysis = chat_utils.chat_with_continuity(voice_analysis_prompt)
            
            # 保存分析结果
            context.set_data('photo_description', voice_analysis)
            context.set_data('voice_only_analysis', True)  # 标记为仅语音分析
            context.response_id = chat_utils.response_id
            
            context.logger.log_step("语音分析", voice_analysis)
            
        except Exception as e:
            context.logger.log_step("错误", f"语音分析失败: {str(e)}")
            self._use_fallback_analysis(context)
    
    def _use_fallback_analysis(self, context):
        """使用备用分析（当所有分析都失败时）"""
        fallback_description = "这是一个充满可能性的地方，在这里可以感受到独特的氛围和美好的体验。"
        context.set_data('photo_description', fallback_description)
        context.set_data('fallback_analysis', True)
        
        context.logger.log_step("备用分析", "使用默认场景描述")
        
        context.oled_display.show_text_oled(
            "分析完成\n使用默认描述\n\n按BT1继续"
        )
        
        context.oled_display.wait_for_button_with_text(
            context.controller,
            "准备继续流程...",
            context=context
        )
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        # 正常情况下进入建议目的地状态
        return DeriveState.SUGGEST_DESTINATION 