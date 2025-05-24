from typing import Optional
import os

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils, encode_image

class AnalyzePhotoState(AbstractState):
    """分析照片状态"""
    
    def __init__(self):
        super().__init__(DeriveState.ANALYZE_PHOTO)
    
    def execute(self, context) -> None:
        """执行分析照片逻辑"""
        context.oled_display.show_text_oled("正在分析\n照片...")
        
        # 获取照片路径
        photo_path = context.get_data('timestamped_image')
        if not photo_path:
            raise Exception("未找到照片进行分析")
        
        # 添加详细调试信息
        context.logger.log_step("🔍 分析照片调试", f"开始分析照片")
        context.logger.log_step("📁 照片路径", f"路径: {photo_path}")
        context.logger.log_step("📁 文件存在检查", f"文件存在: {os.path.exists(photo_path)}")
        
        if os.path.exists(photo_path):
            file_size = os.path.getsize(photo_path)
            context.logger.log_step("📏 文件大小", f"大小: {file_size} bytes")
            
            # 验证图片
            try:
                from PIL import Image
                with Image.open(photo_path) as img:
                    context.logger.log_step("🖼️ 图片验证", f"格式: {img.format}, 尺寸: {img.size}")
            except Exception as e:
                context.logger.log_step("❌ 图片验证失败", f"错误: {str(e)}")
                raise Exception(f"无效的图片文件: {str(e)}")
        
        # 编码图片为base64
        context.logger.log_step("🔄 Base64编码", "开始编码...")
        base64_image = encode_image(photo_path)
        context.logger.log_step("✅ 编码完成", f"长度: {len(base64_image)} 字符")
        
        data_url = f"data:image/jpeg;base64,{base64_image}"
        context.logger.log_step("🔗 Data URL", f"总长度: {len(data_url)} 字符")
        
        # 使用聊天工具分析照片
        chat_utils = DeriveChatUtils(context.response_id)
        
        # 构建分析照片的输入
        input_content = [
            {"type": "input_text", "text": "请详细描述这张照片的内容以及给人带来的感受。"},
            {"type": "input_image", "image_url": data_url}
        ]
        
        context.logger.log_step("📋 输入格式", f"输入包含 {len(input_content)} 个元素")
        context.logger.log_step("🤖 发送请求", "发送到OpenAI...")
        
        # 调用分析
        photo_description = chat_utils.chat_with_continuity(input_content)
        
        context.logger.log_step("📨 AI回复", f"回复长度: {len(photo_description)}")
        context.logger.log_step("📨 AI回复内容", f"完整回复: {photo_description}")
        
        # 检查回复质量
        failure_keywords = ["抱歉", "无法", "不能", "看不到", "无法查看", "cannot", "can't", "sorry", "unable"]
        has_failure = any(keyword in photo_description.lower() for keyword in failure_keywords)
        
        context.logger.log_step("🔍 回复分析", f"包含失败关键词: {has_failure}")
        
        context.set_data('photo_description', photo_description)
        context.response_id = chat_utils.response_id
        
        context.logger.log_step("✅ 照片分析完成", photo_description)
        
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：建议目的地"""
        return DeriveState.SUGGEST_DESTINATION 