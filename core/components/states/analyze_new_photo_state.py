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
            
            # 使用聊天工具分析照片和语音
            chat_utils = DeriveChatUtils(context.response_id)
            
            # 构建综合分析提示
            if voice_text and len(voice_text.strip()) > 0:
                analysis_text = f"""
                请描述这张照片的内容。
                
                用户说了: "{voice_text}"
                
                请描述照片中看到的内容，并结合用户的描述给出整体印象。
                """
            else:
                analysis_text = f"""
                请描述这张照片的内容，包括看到的物体、环境、氛围等。
                """
            
            # 构建包含图片和文本的输入
            input_content = [
                {"type": "input_text", "text": analysis_text},
                {"type": "input_image", "image_url": data_url}
            ]
            
            context.logger.log_step("📝 提示词", f"提示词长度: {len(analysis_text)}")
            context.logger.log_step("📋 输入格式", f"输入包含 {len(input_content)} 个元素")
            context.logger.log_step("📋 输入结构", f"元素1类型: {input_content[0]['type']}, 元素2类型: {input_content[1]['type']}")
            context.logger.log_step("🤖 发送请求", "发送新照片分析到OpenAI...")
            
            response = chat_utils.chat_with_continuity(input_content)
            context.response_id = chat_utils.response_id
            
            context.logger.log_step("📨 AI回复", f"回复长度: {len(response)}")
            context.logger.log_step("📨 AI回复内容", f"完整回复: {response}")
            
            # 检查回复质量
            failure_keywords = ["抱歉", "无法", "不能", "看不到", "无法查看", "cannot", "can't", "sorry", "unable"]
            success_keywords = ["看到", "图片", "照片", "画面", "画中", "see", "image", "photo"]
            
            has_failure_keywords = any(keyword in response.lower() for keyword in failure_keywords)
            has_success_keywords = any(keyword in response.lower() for keyword in success_keywords)
            
            context.logger.log_step("🔍 关键词分析", f"失败关键词: {has_failure_keywords}, 成功关键词: {has_success_keywords}")
            
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