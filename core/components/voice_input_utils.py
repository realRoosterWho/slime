import os
import sys
import time
import threading
from typing import Optional, Tuple

# 导入语音识别模块
try:
    # 尝试导入stt_utils，需要确保路径正确
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    stt_path = os.path.join(project_root, "core", "audio")
    if stt_path not in sys.path:
        sys.path.append(stt_path)
    
    from stt_utils import SpeechToText
    STT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 语音识别模块不可用: {e}")
    STT_AVAILABLE = False

class VoiceInputManager:
    """语音输入管理器 - 处理录音、进度显示和错误处理"""
    
    def __init__(self, context):
        self.context = context
        self.is_recording = False
        self.recording_thread = None
        self.progress_thread = None
        self.recorded_text = None
        self.recording_error = None
        
        # 录音配置
        self.recording_config = {
            'duration': 25,          # 录音时长（改为25秒，与拍照+语音模式一致）
            'language': 'zh-CN',     # 语言
            'channels': 1            # 单声道
        }
    
    def record_mood_voice(self, duration: int = 25) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        录制心情语音
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (成功标志, 识别文本, 错误信息)
        """
        if not STT_AVAILABLE:
            error_msg = "语音识别功能不可用"
            self.context.logger.log_step("语音错误", error_msg)
            return False, None, error_msg

        try:
            self.context.logger.log_step("语音输入", f"开始录制用户心情，时长{duration}秒")
            
            # 显示录音准备界面
            self._show_recording_preparation()
            
            # 等待用户确认开始录音
            result = self.context.oled_display.wait_for_button_with_text(
                self.context.controller,
                "准备录音...\n说出你的心情状态\n按BT1开始录音",
                context=self.context
            )
            
            # 检查长按返回菜单
            if result == 2:
                self.context.logger.log_step("用户操作", "用户长按返回菜单")
                return False, None, "用户取消录音"
            
            # 录音循环，支持重录
            max_attempts = 3
            attempt = 1
            
            while attempt <= max_attempts:
                self.context.logger.log_step("录音尝试", f"第 {attempt} 次录音尝试")
                
                # 重置状态
                self.is_recording = False
                self.recorded_text = None
                self.recording_error = None
                
                # 开始录音和进度显示
                success = self._start_recording_with_progress(duration)
                
                if success and self.recorded_text:
                    # 显示录音结果并等待用户确认
                    user_action = self._show_recording_result()
                    
                    if user_action == 'confirm':
                        # 用户确认，返回成功
                        self.context.logger.log_step("语音识别结果", f"原始文本: {self.recorded_text}")
                        return True, self.recorded_text, None
                    elif user_action == 'retry':
                        # 用户要求重录
                        self.context.logger.log_step("用户操作", f"用户要求重录 (第{attempt}次)")
                        attempt += 1
                        if attempt <= max_attempts:
                            self.context.oled_display.show_text_oled("准备重新录音...")
                            time.sleep(1)
                        continue
                    elif user_action == 'menu':
                        # 用户要求返回菜单
                        return False, None, "用户返回菜单"
                else:
                    # 录音失败
                    error_msg = self.recording_error or "录音或识别失败"
                    self.context.logger.log_step("录音失败", f"第{attempt}次录音失败: {error_msg}")
                    
                    if attempt < max_attempts:
                        # 询问是否重试
                        retry_result = self.context.oled_display.wait_for_button_with_text(
                            self.context.controller,
                            f"录音失败\n{error_msg}\n\n按BT1重试 BT2跳过",
                            context=self.context
                        )
                        
                        if retry_result == 2:  # 长按返回菜单
                            return False, None, "用户返回菜单"
                        elif hasattr(self.context.controller, 'last_button'):
                            if self.context.controller.last_button == 'BTN1':
                                attempt += 1
                                continue
                            elif self.context.controller.last_button == 'BTN2':
                                return False, None, "用户跳过录音"
                        else:
                            attempt += 1
                            continue
                    else:
                        # 达到最大尝试次数
                        return False, None, error_msg
            
            # 达到最大尝试次数仍然失败
            return False, None, "录音重试次数已达上限"
                
        except Exception as e:
            error_msg = f"语音录制异常: {str(e)}"
            self.context.logger.log_step("语音错误", error_msg)
            return False, None, error_msg
    
    def _show_recording_preparation(self):
        """显示录音准备界面"""
        self.context.oled_display.show_text_oled(
            "说出你的心情\nBT1开始录音\nBT2默认心情"
        )
        time.sleep(1)
    
    def _start_recording_with_progress(self, duration: int) -> bool:
        """启动录音并显示进度"""
        try:
            # 启动录音线程
            self.recording_thread = threading.Thread(
                target=self._recording_worker, 
                args=(duration,)
            )
            
            # 启动进度显示线程
            self.progress_thread = threading.Thread(
                target=self._progress_worker, 
                args=(duration,)
            )
            
            # 显示开始提示
            self.context.oled_display.show_text_oled("即将开始录音\n准备说话...")
            time.sleep(1)
            
            # 开始录音
            self.is_recording = True
            self.recording_thread.start()
            self.progress_thread.start()
            
            # 等待录音完成
            self.recording_thread.join()
            self.progress_thread.join()
            
            return self.recorded_text is not None
            
        except Exception as e:
            self.recording_error = f"录音过程异常: {str(e)}"
            self.is_recording = False
            return False
    
    def _recording_worker(self, duration: int):
        """录音工作线程"""
        try:
            # 创建语音识别实例
            stt = SpeechToText(
                language_code=self.recording_config['language'],
                channels=self.recording_config['channels']
            )
            
            # 开始录音识别
            self.recorded_text = stt.record_and_transcribe(duration=duration)
            
        except Exception as e:
            self.recording_error = f"录音失败: {str(e)}"
            self.recorded_text = None
        finally:
            self.is_recording = False
    
    def _progress_worker(self, duration: int):
        """进度显示工作线程"""
        start_time = time.time()
        
        while self.is_recording:
            elapsed_time = time.time() - start_time
            
            if elapsed_time >= duration:
                break
                
            # 更新进度显示
            progress_text = self._generate_progress_text(elapsed_time, duration)
            self.context.oled_display.show_text_oled(progress_text)
            
            # 记录进度日志（每2秒记录一次）
            if int(elapsed_time) % 2 == 0 and elapsed_time > 0:
                self.context.logger.log_step("录音进度", f"已录制 {elapsed_time:.1f} 秒")
            
            time.sleep(0.5)  # 0.5秒更新一次显示
        
        # 显示录音完成
        if self.is_recording or elapsed_time >= duration:
            self.context.oled_display.show_text_oled(
                "录音完成\n正在识别...\n[########] 100%"
            )
    
    def _generate_progress_text(self, elapsed_time: float, total_duration: int) -> str:
        """生成进度显示文本 - 简化版本，只占用3行"""
        progress = min(elapsed_time / total_duration, 1.0)
        bar_length = 8  # 缩短进度条长度
        filled_length = int(bar_length * progress)
        
        # 进度条: [####----] 50%
        bar = '#' * filled_length + '-' * (bar_length - filled_length)
        percentage = int(progress * 100)
        
        remaining_time = max(0, total_duration - elapsed_time)
        
        # 简化为3行显示
        display_text = f"录音 {elapsed_time:.0f}/{total_duration}秒\n"
        display_text += f"[{bar}] {percentage}%\n"
        display_text += f"剩余 {remaining_time:.0f} 秒"
        
        return display_text
    
    def _show_recording_result(self) -> str:
        """
        显示录音识别结果并等待用户确认
        
        Returns:
            str: 用户选择 ('confirm', 'retry', 'menu')
        """
        if not self.recorded_text:
            return 'retry'
            
        # 截断过长的文本用于显示
        display_text = self.recorded_text
        if len(display_text) > 80:
            display_text = display_text[:77] + "..."
        
        result_display = f"识别结果:\n{display_text}\n按BT1确认 BT2重录"
        
        # 等待用户确认
        result = self.context.oled_display.wait_for_button_with_text(
            self.context.controller,
            result_display,
            context=self.context
        )
        
        # 判断用户选择
        if result == 2:  # 长按返回菜单
            return 'menu'
        elif hasattr(self.context.controller, 'last_button'):
            if self.context.controller.last_button == 'BTN1':
                return 'confirm'
            elif self.context.controller.last_button == 'BTN2':
                return 'retry'
        
        # 默认确认
        return 'confirm'
    
    def handle_recording_error(self, error_type: str, error_msg: str) -> str:
        """
        处理录音错误
        
        Returns:
            str: 用户选择的操作 ('retry', 'skip', 'default')
        """
        error_configs = {
            'microphone_not_found': {
                'message': '未检测到麦克风\n将使用默认心情\n按BT1继续',
                'action': 'default'
            },
            'recording_failed': {
                'message': f'录音失败\n{error_msg}\n\n按BT1重试 BT2跳过',
                'action': 'retry_or_skip'
            },
            'recognition_failed': {
                'message': '语音识别失败\n按BT1重录\n按BT2使用默认心情',
                'action': 'retry_or_default'
            }
        }
        
        config = error_configs.get(error_type, {
            'message': f'出现错误\n{error_msg}\n\n按BT1重试 BT2跳过',
            'action': 'retry_or_skip'
        })
        
        self.context.logger.log_step("语音错误处理", f"{error_type}: {error_msg}")
        
        # 显示错误信息并等待用户选择
        result = self.context.oled_display.wait_for_button_with_text(
            self.context.controller,
            config['message'],
            context=self.context
        )
        
        # 根据按键和配置决定操作
        if config['action'] == 'default':
            return 'default'
        elif result == 2:  # 长按返回菜单
            return 'menu'
        elif hasattr(self.context.controller, 'last_button'):
            if self.context.controller.last_button == 'BTN1':
                return 'retry'
            elif self.context.controller.last_button == 'BTN2':
                return 'skip' if 'skip' in config['action'] else 'default'
        
        return 'default'  # 默认操作
    
    def validate_voice_result(self, text: str) -> bool:
        """验证语音识别结果的有效性"""
        if not text or len(text.strip()) < 2:
            return False
            
        # 检查是否包含有意义的内容（简单检查）
        meaningful_chars = sum(1 for c in text if c.isalnum() or c in '，。！？、')
        return meaningful_chars >= 3
    
    def get_default_mood_text(self) -> str:
        """获取默认心情文本"""
        default_moods = [
            "感觉空气布满了水雾，有一种看不清前方道路的错觉，觉得很放松。想要在这个氛围里面漂流。",
            "今天心情很好，想要探索一些新奇有趣的地方。",
            "感到有些疲惫，希望能找到一个安静美好的地方休息。",
            "充满好奇心，想要发现一些神秘或者有趣的事物。",
            "心情平静，想要体验一段轻松愉快的旅程。"
        ]
        return default_moods[0]  # 返回第一个作为默认 