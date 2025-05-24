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
        """分析照片+语音组合数据 - 多步骤方案"""
        context.oled_display.show_text_oled("正在分析\n照片和语音...")
        
        try:
            # 添加详细的调试信息
            context.logger.log_step("🔍 调试信息", f"开始分析照片+语音")
            context.logger.log_step("📁 照片路径", f"原始路径: {photo_path}")
            context.logger.log_step("🗣️ 语音文本", f"文本长度: {len(voice_text)}, 内容: {voice_text[:100]}...")
            
            # 检查照片文件是否存在
            if not os.path.exists(photo_path):
                raise FileNotFoundError(f"照片文件不存在: {photo_path}")
            
            # 获取绝对路径
            abs_photo_path = os.path.abspath(photo_path)
            context.logger.log_step("📁 绝对路径", f"绝对路径: {abs_photo_path}")
            
            # 检查文件大小
            file_size = os.path.getsize(photo_path)
            context.logger.log_step("📏 文件大小", f"文件大小: {file_size} bytes")
            
            if file_size == 0:
                raise ValueError("照片文件为空")
            
            # 验证是否为有效的图片文件
            try:
                from PIL import Image
                with Image.open(photo_path) as img:
                    img_format = img.format
                    img_mode = img.mode  
                    img_size = img.size
                    context.logger.log_step("🖼️ 图片信息", f"格式: {img_format}, 模式: {img_mode}, 尺寸: {img_size}")
            except Exception as e:
                context.logger.log_step("❌ 图片验证失败", f"不是有效的图片文件: {str(e)}")
                raise ValueError(f"无效的图片文件: {str(e)}")
            
            # 编码照片为base64
            context.logger.log_step("🔄 开始编码", "开始Base64编码...")
            base64_image = encode_image(photo_path)
            base64_length = len(base64_image)
            context.logger.log_step("✅ 编码完成", f"Base64长度: {base64_length} 字符")
            context.logger.log_step("🔤 Base64预览", f"前100字符: {base64_image[:100]}")
            
            # 验证base64编码是否有效
            if base64_length < 100:
                raise ValueError(f"Base64编码异常短: {base64_length} 字符")
            
            # 构建data URL
            data_url = f"data:image/jpeg;base64,{base64_image}"
            data_url_length = len(data_url)
            context.logger.log_step("🔗 Data URL", f"Data URL总长度: {data_url_length} 字符")
            
            # === 第一步：简单描述照片（避免内容过滤） ===
            context.logger.log_step("🎯 第一步", "开始简单照片描述")
            
            chat_utils = DeriveChatUtils(context.response_id)
            
            # 简单描述提示（保证成功）
            simple_description_prompt = "请简单描述这张照片中看到的内容。"
            
            # 构建输入内容
            input_content = [
                {"type": "input_text", "text": simple_description_prompt},
                {"type": "input_image", "image_url": data_url}
            ]
            
            context.logger.log_step("📋 第一步输入", f"输入包含 {len(input_content)} 个元素")
            
            # 调用基本描述
            basic_description = chat_utils.chat_with_continuity(input_content)
            context.response_id = chat_utils.response_id
            
            context.logger.log_step("📨 第一步结果", f"基本描述: {basic_description}")
            
            # 检查基本描述是否成功
            failure_keywords = ["抱歉", "无法", "不能", "看不到", "无法查看", "cannot", "can't", "sorry", "unable"]
            has_failure_keywords = any(keyword in basic_description.lower() for keyword in failure_keywords)
            
            if has_failure_keywords:
                context.logger.log_step("❌ 第一步失败", "基本描述被拒绝，回退到语音分析")
                self._analyze_voice_only(context, voice_text)
                return
            
            # === 第二步：史莱姆个性化分析（基于第一步结果） ===
            context.logger.log_step("🎭 第二步", "开始史莱姆个性化分析")
            context.oled_display.show_text_oled("史莱姆正在\n思考照片...")
            
            # 获取史莱姆属性
            slime_obsession = context.get_slime_attribute('obsession', '寻找有趣的事物')
            slime_tone = context.get_slime_attribute('tone', '友好好奇')
            slime_quirk = context.get_slime_attribute('quirk', '喜欢探索')
            
            # 史莱姆个性化分析提示
            slime_analysis_prompt = f"""
            照片基本内容: {basic_description}
            
            用户同时说了: "{voice_text}"
            
            现在请从史莱姆的角度分析这个场景：
            
            史莱姆的执念: {slime_obsession}
            史莱姆的语气: {slime_tone}
            史莱姆的癖好: {slime_quirk}
            
            请生成一段分析，包含：
            1. 对照片内容的个性化解读
            2. 这个场景是否符合史莱姆的执念
            3. 史莱姆会如何看待这个地方
            4. 结合用户语音的整体感受
            
            请用生动有趣的描述，控制在150字以内。
            """
            
            # 调用史莱姆分析
            slime_analysis = chat_utils.chat_with_continuity(
                system_content="你是一个有独特个性的史莱姆，会从自己的执念角度来分析场景。",
                prompt=slime_analysis_prompt
            )
            context.response_id = chat_utils.response_id
            
            context.logger.log_step("🎭 第二步结果", f"史莱姆分析: {slime_analysis}")
            
            # === 第三步：融合生成最终分析 ===
            final_analysis = f"基本场景: {basic_description}\n\n史莱姆的看法: {slime_analysis}"
            
            # 保存分析结果
            context.set_data('photo_description', final_analysis)
            context.set_data('basic_description', basic_description)  # 保存基本描述备用
            context.set_data('slime_analysis', slime_analysis)  # 保存史莱姆分析备用
            context.set_data('voice_enhanced_analysis', True)  # 标记为语音增强分析
            
            context.logger.log_step("✅ 多步骤分析成功", f"最终分析已生成")
            
        except Exception as e:
            context.logger.log_step("❌ 照片+语音分析错误", f"分析失败: {str(e)}")
            context.logger.log_step("❌ 错误详情", f"错误类型: {type(e).__name__}")
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