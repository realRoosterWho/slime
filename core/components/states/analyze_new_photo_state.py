import base64
from typing import Optional
import os

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
            
            # 添加详细调试信息
            context.logger.log_step("🔍 新照片分析调试", f"开始分析新照片")
            context.logger.log_step("📁 新照片路径", f"路径: {new_photo_path}")
            context.logger.log_step("🗣️ 语音文本", f"长度: {len(voice_text)}, 内容: {voice_text[:50]}...")
            context.logger.log_step("📁 文件存在检查", f"文件存在: {os.path.exists(new_photo_path)}")
            
            if os.path.exists(new_photo_path):
                file_size = os.path.getsize(new_photo_path)
                context.logger.log_step("📏 文件大小", f"大小: {file_size} bytes")
                
                # 验证图片
                try:
                    from PIL import Image
                    with Image.open(new_photo_path) as img:
                        context.logger.log_step("🖼️ 图片验证", f"格式: {img.format}, 尺寸: {img.size}")
                except Exception as e:
                    context.logger.log_step("❌ 图片验证失败", f"错误: {str(e)}")
                    raise ValueError(f"无效的图片文件: {str(e)}")
            
            # 编码图片为base64
            context.logger.log_step("🔄 Base64编码", "开始编码...")
            base64_image = encode_image(new_photo_path)
            context.logger.log_step("✅ 编码完成", f"长度: {len(base64_image)} 字符")
            
            data_url = f"data:image/jpeg;base64,{base64_image}"
            context.logger.log_step("🔗 Data URL", f"总长度: {len(data_url)} 字符")
            
            context.logger.log_step("分析新照片+语音", f"开始分析新照片: {new_photo_path}, 语音长度: {len(voice_text)}")
            
            # 获取史莱姆的执念和属性
            slime_obsession = context.get_slime_attribute('obsession')
            slime_tone = context.get_slime_attribute('tone')
            
            context.logger.log_step("🤖 史莱姆属性", f"执念: {slime_obsession}, 语气: {slime_tone}")
            
            # === 第一步：简单描述新照片（避免内容过滤） ===
            context.logger.log_step("🎯 第一步", "开始简单新照片描述")
            
            # 使用聊天工具分析照片和语音
            chat_utils = DeriveChatUtils(context.response_id)
            
            # 第一步：简单描述提示
            simple_description_prompt = "请简单描述这张照片中看到的内容。"
            
            # 构建包含图片和文本的输入
            input_content = [
                {"type": "input_text", "text": simple_description_prompt},
                {"type": "input_image", "image_url": data_url}
            ]
            
            context.logger.log_step("📋 第一步输入", f"输入包含 {len(input_content)} 个元素")
            context.logger.log_step("🤖 发送请求", "发送第一步简单描述到OpenAI...")
            
            basic_description = chat_utils.chat_with_continuity(input_content)
            context.response_id = chat_utils.response_id
            
            context.logger.log_step("📨 第一步结果", f"基本描述: {basic_description}")
            
            # 检查第一步是否成功
            failure_keywords = ["抱歉", "无法", "不能", "看不到", "无法查看", "cannot", "can't", "sorry", "unable"]
            has_failure_keywords = any(keyword in basic_description.lower() for keyword in failure_keywords)
            
            if has_failure_keywords:
                context.logger.log_step("❌ 第一步失败", "基本描述被拒绝，使用默认分析")
                # 设置默认分析结果
                voice_text = context.get_data('new_photo_voice_text', '')
                if voice_text:
                    default_analysis = f"听了你的描述，看起来很有意思！让我想想这能带来什么奖励..."
                else:
                    default_analysis = "看起来很有趣，让我想想这能带来什么奖励..."
                context.set_data('new_photo_analysis', default_analysis)
                return
            
            # === 第二步：史莱姆个性化分析新照片 ===
            context.logger.log_step("🎭 第二步", "开始史莱姆新照片分析")
            context.oled_display.show_text_oled("史莱姆在想\n这符合执念吗...")
            
            # 构建史莱姆分析提示
            if voice_text and len(voice_text.strip()) > 0:
                slime_new_analysis_prompt = f"""
                新照片基本内容: {basic_description}
                
                用户说了: "{voice_text}"
                
                史莱姆的执念: {slime_obsession}
                史莱姆的语气: {slime_tone}
                
                请从史莱姆的角度分析这个新探索的地方：
                1. 这个地方有什么特别之处
                2. 是否符合史莱姆的执念
                3. 史莱姆会有什么想法和反应
                4. 结合用户的描述，整体印象如何
                
                请用史莱姆的口吻回答，控制在120字以内。
                """
            else:
                slime_new_analysis_prompt = f"""
                新照片内容: {basic_description}
                
                史莱姆的执念: {slime_obsession}
                史莱姆的语气: {slime_tone}
                
                请从史莱姆的角度分析这个新探索的地方：
                1. 这个地方有什么特别之处
                2. 是否符合史莱姆的执念
                3. 史莱姆会有什么想法和反应
                
                请用史莱姆的口吻回答，控制在100字以内。
                """
            
            # 调用史莱姆新照片分析
            slime_new_analysis = chat_utils.chat_with_continuity(
                system_content="你是一个有个性和执念的史莱姆，会从自己的角度分析新探索的场景。",
                prompt=slime_new_analysis_prompt
            )
            context.response_id = chat_utils.response_id
            
            context.logger.log_step("🎭 第二步结果", f"史莱姆新分析: {slime_new_analysis}")
            
            # === 第三步：融合生成最终新照片分析 ===
            final_new_analysis = f"场景描述: {basic_description}\n\n史莱姆的反应: {slime_new_analysis}"
            
            # 保存新照片分析结果
            context.set_data('new_photo_analysis', final_new_analysis)
            context.set_data('new_basic_description', basic_description)  # 保存基本描述备用
            context.set_data('new_slime_analysis', slime_new_analysis)  # 保存史莱姆分析备用
            
            # 记录分析结果
            analysis_type = "新照片+语音多步骤分析" if voice_text else "新照片多步骤分析"
            context.logger.log_step(f"✅ {analysis_type}", f"分析完成: {slime_new_analysis[:50]}...")
            
            # 显示分析结果，重点展示史莱姆的反应
            if voice_text and len(voice_text.strip()) > 0:
                display_text = f"史莱姆听了你的话\n看了照片后说：\n{slime_new_analysis[:60]}..."
            else:
                display_text = f"史莱姆看了看：\n{slime_new_analysis[:80]}..."
                
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