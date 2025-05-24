import json
from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils

class AnalyzeRewardState(AbstractState):
    """分析奖励状态"""
    
    def __init__(self):
        super().__init__(DeriveState.ANALYZE_REWARD)
    
    def execute(self, context) -> None:
        """执行分析奖励逻辑"""
        context.oled_display.show_text_oled("史莱姆在想\n给什么奖励...")
        
        try:
            # 获取新照片分析结果和史莱姆属性
            new_photo_analysis = context.get_data('new_photo_analysis', '')
            slime_obsession = context.get_slime_attribute('obsession')
            slime_tone = context.get_slime_attribute('tone')
            original_photo_analysis = context.get_data('photo_description', '')
            
            # 使用聊天工具分析奖励
            chat_utils = DeriveChatUtils(context.response_id)
            
            reward_prompt = f"""
            作为一个有执念的史莱姆，我需要根据这张新照片给出合适的奖励。
            
            我的执念: {slime_obsession}
            我的语气: {slime_tone}
            原始照片分析: {original_photo_analysis}
            新照片分析: {new_photo_analysis}
            
            请帮我决定:
            1. 这次探索是否成功符合了我的执念？
            2. 应该给出什么样的奖励？（符合执念程度越高，奖励越好）
            3. 奖励的具体内容是什么？
            
            奖励类型选择:
            - "great": 符合执念，给出奖励，比如某种神秘装扮或者符合执念的物件之类的
            - "encouragement": 不太符合，给出意外奖励，符合当前风景的一个史莱姆蛋
            
            回复格式:
            {{
                "reward_level": "奖励等级",
                "reward_description": "奖励描述",
                "reward_reason": "给出这个奖励的原因"
            }}
            """
            
            response = chat_utils.chat_with_continuity(
                system_content="你是一个会根据照片符合程度给出奖励的史莱姆，你有自己的执念和判断标准。",
                prompt=reward_prompt
            )
            context.response_id = chat_utils.response_id
            
            # 解析奖励分析结果
            reward_data = self._parse_reward_response(response)
            
            # 保存奖励分析结果
            context.set_data('reward_level', reward_data.get('reward_level', 'encouragement'))
            context.set_data('reward_description', reward_data.get('reward_description', '一个小小的奖励'))
            context.set_data('reward_reason', reward_data.get('reward_reason', '感谢你的探索'))
            
            context.logger.log_step(
                "分析奖励",
                f"奖励等级: {reward_data.get('reward_level')}, 描述: {reward_data.get('reward_description')}"
            )
            
            # 显示奖励决定过程
            display_text = f"史莱姆想了想：\n{reward_data.get('reward_reason', '你做得很好')}..."
            result = context.oled_display.wait_for_button_with_text(
                context.controller,
                display_text,
                context=context  # 传入context用于长按检测
            )
            
            # 检查是否是长按返回菜单
            if result == 2:
                context.logger.log_step("用户操作", "用户长按按钮2返回菜单")
                return
            
        except Exception as e:
            context.logger.log_step("错误", f"分析奖励失败: {str(e)}")
            
            # 设置默认奖励
            context.set_data('reward_level', 'encouragement')
            context.set_data('reward_description', '一个神秘的奖励')
            context.set_data('reward_reason', '感谢你的陪伴和探索')
            
            result = context.oled_display.wait_for_button_with_text(
                context.controller,
                "史莱姆想了想：\n谢谢你的探索...",
                context=context  # 传入context用于长按检测
            )
            
            # 检查是否是长按返回菜单
            if result == 2:
                context.logger.log_step("用户操作", "用户长按按钮2返回菜单")
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        return DeriveState.GENERATE_REWARD_IMAGE
    
    def _parse_reward_response(self, response_text):
        """解析奖励响应"""
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
            return {
                "reward_level": "encouragement",
                "reward_description": "一个小小的奖励",
                "reward_reason": "感谢你的探索"
            } 