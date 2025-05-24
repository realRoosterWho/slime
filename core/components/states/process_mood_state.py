from typing import Optional

from ..abstract_state import AbstractState
from ..derive_states import DeriveState
from ..derive_utils import DeriveChatUtils

class ProcessMoodState(AbstractState):
    """处理心情语音状态"""
    
    def __init__(self):
        super().__init__(DeriveState.PROCESS_MOOD)
    
    def execute(self, context) -> None:
        """执行心情处理逻辑"""
        context.logger.log_step("心情处理状态", "开始处理用户心情")
        
        try:
            # 获取原始语音文本
            raw_voice_text = context.get_data('raw_voice_text', '')
            is_voice_input = context.get_data('is_voice_input', True)
            
            if not raw_voice_text:
                raise Exception("未找到语音文本数据")
            
            context.logger.log_step("原始文本", f"输入文本: {raw_voice_text}")
            
            # 显示处理中界面
            self._show_processing_message(context, is_voice_input)
            
            if is_voice_input:
                # 语音输入需要GPT处理
                processed_mood = self._process_voice_with_gpt(context, raw_voice_text)
            else:
                # 默认文本直接使用
                processed_mood = raw_voice_text
                context.logger.log_step("心情处理", "使用默认心情，跳过GPT处理")
            
            if processed_mood:
                # 保存处理后的心情
                self._save_processed_mood(context, processed_mood)
                
                # 显示处理结果
                self._show_processing_result(context, processed_mood)
                
                context.logger.log_step("心情处理完成", f"最终心情: {processed_mood[:50]}...")
            else:
                # 处理失败，使用原始文本
                self._save_processed_mood(context, raw_voice_text)
                context.logger.log_step("心情处理", "GPT处理失败，使用原始文本")
                
        except Exception as e:
            context.logger.log_step("错误", f"心情处理失败: {str(e)}")
            
            # 使用默认的心情文本
            default_mood = "感觉空气布满了水雾，有一种看不清前方道路的错觉，觉得很放松。想要在这个氛围里面漂流。"
            self._save_processed_mood(context, default_mood)
            
            context.oled_display.show_text_oled(
                "⚠️ 处理过程出现问题\n\n"
                "已为你设置默认心情\n"
                "继续漂流旅程..."
            )
            context.sleep(2)
    
    def _show_processing_message(self, context, is_voice_input: bool):
        """显示处理中信息"""
        if is_voice_input:
            message = "🧠 正在分析心情...\n\n通过AI理解你的\n真实感受..."
        else:
            message = "📝 正在准备心情...\n\n为你设置完美的\n漂流状态..."
        
        context.oled_display.show_text_oled(message)
        context.sleep(1)
    
    def _process_voice_with_gpt(self, context, raw_voice_text: str) -> Optional[str]:
        """使用GPT处理语音文本"""
        try:
            context.logger.log_step("GPT心情提取", "开始调用GPT处理心情")
            
            # 显示GPT处理进度
            context.oled_display.show_text_oled(
                "🤖 AI正在分析...\n\n"
                "理解你的心情状态\n"
                "优化表达方式..."
            )
            
            # 使用聊天工具处理心情
            chat_utils = DeriveChatUtils(context.response_id)
            
            processed_mood = chat_utils.generate_text(
                'mood_extraction',
                raw_voice_text=raw_voice_text
            )
            
            context.response_id = chat_utils.response_id
            
            # 验证处理结果
            if self._validate_mood_result(processed_mood):
                context.logger.log_step("GPT处理成功", f"处理后心情: {processed_mood}")
                return processed_mood.strip()
            else:
                context.logger.log_step("GPT处理异常", f"结果验证失败: {processed_mood}")
                return None
                
        except Exception as e:
            context.logger.log_step("GPT处理错误", f"心情提取失败: {str(e)}")
            return None
    
    def _validate_mood_result(self, mood_text: str) -> bool:
        """验证心情提取结果"""
        if not mood_text or len(mood_text.strip()) < 10:
            return False
        
        # 检查是否包含基本的情感描述
        emotion_keywords = ['心情', '感觉', '想要', '希望', '觉得', '感到', '情绪', '状态']
        return any(keyword in mood_text for keyword in emotion_keywords)
    
    def _save_processed_mood(self, context, processed_mood: str):
        """保存处理后的心情"""
        # 保存到context中，供后续状态使用
        context.set_data('initial_text', processed_mood)
        context.set_data('processed_mood', processed_mood)
        
        # 记录到日志
        context.logger.log_step("心情保存", f"已保存处理后心情: {processed_mood[:100]}...")
    
    def _show_processing_result(self, context, processed_mood: str):
        """显示处理结果"""
        # 显示优化后的心情
        display_text = processed_mood
        if len(display_text) > 100:
            display_text = display_text[:97] + "..."
        
        result = context.oled_display.wait_for_button_with_text(
            context.controller,
            f"✨ 心情分析完成\n\n{display_text}\n\n按BT1开始生成史莱姆",
            context=context
        )
        
        # 检查长按返回菜单
        if result == 2:
            context.logger.log_step("用户操作", "用户长按返回菜单")
            return
        
        # 显示即将开始的提示
        context.oled_display.show_text_oled(
            "🎨 准备生成史莱姆...\n\n"
            "根据你的心情\n"
            "创造专属角色..."
        )
        context.sleep(2)
    
    def get_next_state(self, context) -> Optional[DeriveState]:
        """返回下一个状态"""
        if context.should_return_to_menu():
            return DeriveState.EXIT
        
        # 检查是否有处理后的心情
        if context.get_data('initial_text'):
            return DeriveState.INIT
        else:
            # 没有有效心情，返回菜单
            return DeriveState.EXIT 