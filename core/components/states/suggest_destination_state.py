import json
from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils

class SuggestDestinationState(AbstractState):
    """建议目的地状态"""
    
    def __init__(self):
        super().__init__(DeriveState.SUGGEST_DESTINATION)
    
    def execute(self, context) -> None:
        """执行建议目的地逻辑"""
        context.oled_display.show_text_oled("正在思考\n建议...")
        
        try:
            # 使用聊天工具生成建议
            chat_utils = DeriveChatUtils(context.response_id)
            
            # 生成更具体的建议
            suggestion_prompt = f"""
            基于照片内容和史莱姆的执念，生成一个具体的建议，引导玩家寻找符合执念的场景。
            
            照片内容: {context.get_data('photo_description')}
            史莱姆执念: {context.get_slime_attribute('obsession')}
            互动语气: {context.get_slime_attribute('tone')}
            
            请提供:
            1. 一个简短的建议(不超过20个字)
            2. 一个简短的理由，为什么这个方向与执念相关
            
            回复格式:
            {{"suggestion": "建议", "reason": "理由"}}
            """
            
            response = chat_utils.chat_with_continuity(
                system_content="你是一个善于引导探索的史莱姆，你会根据照片内容和自己的执念，给出有针对性的建议。",
                prompt=suggestion_prompt
            )
            context.response_id = chat_utils.response_id
            
            # 解析响应
            suggestion_data = self._parse_suggestion_response(response)
            suggestion = suggestion_data.get("suggestion", "去寻找更多有趣的东西吧！")
            reason = suggestion_data.get("reason", "")
            
            # 记录建议
            context.set_data('destination_suggestion', suggestion)
            context.logger.log_step("建议目的地", f"建议: {suggestion}, 理由: {reason}")
            
            # 显示建议和理由
            display_text = f"史莱姆说：\n{suggestion}"
            if reason and len(reason) < 30:  # 如果理由不太长，也一并显示
                display_text += f"\n\n{reason}"
            
            self._wait_for_button(context, display_text)
            
        except Exception as e:
            # 使用备用建议
            context.logger.log_step("错误", f"生成建议时出错: {str(e)}")
            
            default_suggestion = "去寻找更多有趣的东西吧！"
            context.set_data('destination_suggestion', default_suggestion)
            context.logger.log_step("建议目的地", f"使用默认建议: {default_suggestion}")
            self._wait_for_button(context, f"史莱姆说：\n{default_suggestion}")
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：等待新照片"""
        return DeriveState.WAIT_FOR_NEW_PHOTO
    
    def _parse_suggestion_response(self, response_text):
        """解析建议响应"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 尝试提取花括号内的内容
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx+1]
                    return json.loads(json_str)
            except:
                pass
            
            # 解析失败，返回默认值
            return {"suggestion": "去寻找更多有趣的东西吧！", "reason": "可能会符合我的执念"}
    
    def _wait_for_button(self, context, text):
        """等待按钮按下"""
        context.oled_display.wait_for_button_with_text(
            context.controller,
            text
        ) 