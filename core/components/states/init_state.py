import time
from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils

class InitState(AbstractState):
    """初始化状态：生成史莱姆性格和外观"""
    
    def __init__(self):
        super().__init__(DeriveState.INIT)
    
    def execute(self, context) -> None:
        """执行初始化逻辑"""
        context.logger.log_step("初始化", "根据文本开始新的漂流...")
        
        # 显示初始化状态
        context.oled_display.show_text_oled("正在生成\n史莱姆性格...")
        
        # 使用聊天工具生成性格
        chat_utils = DeriveChatUtils(context.response_id)
        
        # 生成史莱姆性格
        personality = chat_utils.generate_text(
            'personality', 
            text=context.initial_text
        )
        context.set_data('personality', personality)
        context.response_id = chat_utils.response_id
        context.logger.log_step("性格生成", personality)
        
        # 提取史莱姆属性
        self._extract_slime_attributes(context, personality, chat_utils)
        
        # 生成视觉描述
        context.oled_display.show_text_oled("正在生成\n外观描述...")
        slime_description = chat_utils.generate_text(
            'slime_description', 
            text=personality
        )
        context.set_data('slime_description', slime_description)
        context.response_id = chat_utils.response_id
        context.logger.log_step("外观描述", slime_description)
        
        # 保存详细的外观描述用于保持一致性
        slime_appearance = f"一个可爱的史莱姆生物。{slime_description}。"
        context.set_data('slime_appearance', slime_appearance)
        context.logger.log_step("一致性外观描述", slime_appearance)
        
        context.oled_display.show_text_oled("性格设定完成")
        time.sleep(1)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态：生成史莱姆图片"""
        return DeriveState.GEN_SLIME_IMAGE
    
    def _extract_slime_attributes(self, context, personality_text: str, chat_utils) -> None:
        """从性格描述中提取史莱姆的属性"""
        context.oled_display.show_text_oled("正在提取\n性格属性...")
        
        # 属性提取提示词
        prompt = f"""
        请从以下史莱姆的性格描述中提取四个关键属性。你的回复必须是严格的JSON格式，不要添加任何其他文本、标记或注释。
        
        性格描述:
        {personality_text}
        
        请仅返回以下JSON格式(不要有任何其他内容，如markdown标记、代码块等):
        {{
            "obsession": "执念内容",
            "quirk": "幻想癖好内容", 
            "reflex": "偏执反应内容",
            "tone": "互动语气内容"
        }}
        """
        
        try:
            # 多次尝试提取，最多尝试3次
            for attempt in range(3):
                try:
                    response = chat_utils.chat_with_continuity(
                        system_content="你是一个数据提取助手。你的任务是准确提取文本中的关键信息，并以JSON格式返回，不添加任何其他内容，如代码块标记、注释等。",
                        prompt=prompt
                    )
                    context.response_id = chat_utils.response_id
                    
                    # 解析JSON响应
                    attributes = chat_utils.parse_json_response(response)
                    
                    # 验证所有必需的键是否存在
                    required_keys = ['obsession', 'quirk', 'reflex', 'tone']
                    missing_keys = [key for key in required_keys if not attributes.get(key)]
                    
                    if not missing_keys:
                        # 所有属性都已提取成功
                        for attr in required_keys:
                            context.set_slime_attribute(attr, attributes[attr])
                        context.logger.log_step("属性提取", f"成功提取史莱姆属性: {context.data['slime_attributes']}")
                        return
                    elif attempt < 2:
                        context.logger.log_step("属性提取", f"提取不完整，缺少: {missing_keys}，尝试重新提取")
                        continue
                
                except Exception as e:
                    if attempt < 2:
                        context.logger.log_step("属性提取", f"JSON解析失败，尝试重新提取: {str(e)}")
                        continue
            
            # 如果多次尝试后仍未成功，使用默认值
            context.logger.log_step("属性提取", "使用默认属性值")
            self._set_default_attributes(context)
                
        except Exception as e:
            context.logger.log_step("属性提取错误", f"提取属性时出错: {e}")
            self._set_default_attributes(context)
    
    def _set_default_attributes(self, context) -> None:
        """设置默认的史莱姆属性"""
        default_attributes = {
            'obsession': '寻找美丽和独特的事物',
            'quirk': '兴奋地跳跃并记录下来',
            'reflex': '好奇地观察并寻找其他有趣的特点',
            'tone': '友好热情，充满好奇'
        }
        
        for attr, value in default_attributes.items():
            context.set_slime_attribute(attr, value)
        
        context.logger.log_step("属性提取", f"使用默认属性值: {context.data['slime_attributes']}") 