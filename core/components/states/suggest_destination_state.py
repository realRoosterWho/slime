import json
from typing import Optional
import time

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
            # 分析错误类型，提供更好的用户体验
            error_msg = str(e)
            context.logger.log_step("错误", f"生成建议时出错: {error_msg}")
            
            # 检查是否是API服务器问题
            server_error_keywords = ["502", "503", "504", "Bad gateway", "Service Unavailable", "Connection error"]
            is_server_error = any(keyword in error_msg for keyword in server_error_keywords)
            
            if is_server_error:
                context.logger.log_step("API服务器问题", "检测到OpenAI API服务器故障，使用智能默认建议")
                context.oled_display.show_text_oled("API服务暂时\n不可用\n生成默认建议...")
                time.sleep(2)
            
            # 生成智能默认建议（基于史莱姆执念）
            slime_obsession = context.get_slime_attribute('obsession', '寻找有趣的事物')
            slime_tone = context.get_slime_attribute('tone', '友好好奇')
            
            # 根据执念生成更个性化的默认建议
            if '颜色' in slime_obsession or '光' in slime_obsession:
                smart_suggestion = "去寻找有特殊光影的地方"
                reason = "那里可能有我想要的色彩"
            elif '水' in slime_obsession or '雨' in slime_obsession:
                smart_suggestion = "去探索有水的环境"
                reason = "水总是藏着秘密"
            elif '夜' in slime_obsession or '星' in slime_obsession:
                smart_suggestion = "等待夜晚来临时再探索"
                reason = "夜色中有我的执念"
            elif '花' in slime_obsession or '植物' in slime_obsession:
                smart_suggestion = "去寻找有植物的地方"
                reason = "自然中藏着我要的东西"
            else:
                smart_suggestion = "继续探索周围的环境"
                reason = "总会找到符合我执念的地方"
            
            context.set_data('destination_suggestion', smart_suggestion)
            context.logger.log_step("智能默认建议", f"建议: {smart_suggestion}, 理由: {reason}")
            
            # 显示智能建议
            if is_server_error:
                display_text = f"史莱姆想了想：\n{smart_suggestion}\n\n(AI服务暂时不可用)"
            else:
                display_text = f"史莱姆说：\n{smart_suggestion}\n\n{reason}"
            
            self._wait_for_button(context, display_text)
    
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
            text,
            context=context
        ) 