from typing import Optional

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
        
        # 编码图片为base64
        base64_image = encode_image(photo_path)
        data_url = f"data:image/jpeg;base64,{base64_image}"
        
        # 使用聊天工具分析照片
        chat_utils = DeriveChatUtils(context.response_id)
        
        # 构建分析照片的输入
        input_content = [
            {"type": "input_text", "text": "请详细描述这张照片的内容以及给人带来的感受。"},
            {"type": "input_image", "image_url": data_url}
        ]
        
        # 调用分析
        photo_description = chat_utils.chat_with_continuity(input_content)
        context.set_data('photo_description', photo_description)
        context.response_id = chat_utils.response_id
        
        context.logger.log_step("照片分析", photo_description)
        
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：建议目的地"""
        return DeriveState.SUGGEST_DESTINATION 