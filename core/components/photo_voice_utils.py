import os
import sys
import time
import threading
from typing import Optional, Tuple

# 导入语音识别模块
try:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    stt_path = os.path.join(project_root, "core", "audio")
    if stt_path not in sys.path:
        sys.path.append(stt_path)
    
    from stt_utils import SpeechToText
    STT_AVAILABLE = True
except ImportError as e:
    print(f"语音识别模块不可用: {e}")
    STT_AVAILABLE = False

# 导入相机模块
from .derive_utils import run_camera_test

class PhotoVoiceManager:
    """拍照+语音录制管理器 - 处理15秒拍照倒计时和并行语音录制"""
    
    def __init__(self, context):
        self.context = context
        self.is_countdown_active = False
        self.is_voice_recording = False
        self.countdown_thread = None
        self.voice_thread = None
        self.progress_thread = None
        
        # 录制配置
        self.photo_countdown = 15  # 15秒拍照倒计时
        self.voice_duration = 12   # 语音录制12秒（在倒计时期间）
        
        # 结果存储
        self.photo_taken = False
        self.voice_text = None
        self.voice_error = None
        
    def take_photo_with_voice(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        执行15秒拍照倒计时 + 并行语音录制
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (拍照成功, 语音文本, 错误信息)
        """
        try:
            self.context.logger.log_step("拍照+语音", "开始15秒拍照倒计时和语音录制")
            
            # 重置状态
            self._reset_state()
            
            # 显示准备界面
            self._show_preparation()
            
            # 等待用户确认开始
            result = self.context.oled_display.wait_for_button_with_text(
                self.context.controller,
                "准备拍照+语音\n\n15秒倒计时摆pose\n同时说出感受\n\n按BT1开始",
                context=self.context
            )
            
            # 检查长按返回菜单
            if result == 2:
                self.context.logger.log_step("用户操作", "用户长按返回菜单")
                return False, None, "用户取消操作"
            
            # 开始倒计时和录音
            success = self._start_photo_voice_process()
            
            if success:
                self.context.logger.log_step("拍照+语音完成", f"照片: {self.photo_taken}, 语音: {self.voice_text[:50] if self.voice_text else 'None'}...")
                return self.photo_taken, self.voice_text, None
            else:
                error_msg = self.voice_error or "拍照或语音录制失败"
                self.context.logger.log_step("拍照+语音错误", error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"拍照+语音异常: {str(e)}"
            self.context.logger.log_step("拍照+语音错误", error_msg)
            return False, None, error_msg
    
    def _reset_state(self):
        """重置内部状态"""
        self.is_countdown_active = False
        self.is_voice_recording = False
        self.photo_taken = False
        self.voice_text = None
        self.voice_error = None
    
    def _show_preparation(self):
        """显示准备界面"""
        self.context.oled_display.show_text_oled(
            "拍照+语音模式\n准备摆pose\n并描述感受"
        )
        time.sleep(2)
    
    def _start_photo_voice_process(self) -> bool:
        """启动拍照倒计时和语音录制"""
        try:
            # 启动拍照倒计时线程
            self.countdown_thread = threading.Thread(
                target=self._photo_countdown_worker
            )
            
            # 启动语音录制线程（如果可用）
            if STT_AVAILABLE:
                self.voice_thread = threading.Thread(
                    target=self._voice_recording_worker
                )
            
            # 启动进度显示线程
            self.progress_thread = threading.Thread(
                target=self._progress_display_worker
            )
            
            # 显示开始提示
            self.context.oled_display.show_text_oled("3秒后开始\n准备摆pose...")
            time.sleep(3)
            
            # 开始所有线程
            self.is_countdown_active = True
            if STT_AVAILABLE:
                self.is_voice_recording = True
            
            self.countdown_thread.start()
            if STT_AVAILABLE and self.voice_thread:
                self.voice_thread.start()
            self.progress_thread.start()
            
            # 等待所有线程完成
            self.countdown_thread.join()
            if STT_AVAILABLE and self.voice_thread:
                self.voice_thread.join()
            self.progress_thread.join()
            
            return self.photo_taken
            
        except Exception as e:
            self.voice_error = f"拍照+语音过程异常: {str(e)}"
            self._stop_all_processes()
            return False
    
    def _photo_countdown_worker(self):
        """拍照倒计时工作线程"""
        try:
            countdown = self.photo_countdown
            
            while countdown > 0 and self.is_countdown_active:
                time.sleep(1)
                countdown -= 1
            
            if self.is_countdown_active:
                # 倒计时结束，拍照
                self.context.logger.log_step("拍照", "倒计时结束，开始拍照")
                run_camera_test()
                self.photo_taken = True
                
        except Exception as e:
            self.voice_error = f"拍照失败: {str(e)}"
            self.photo_taken = False
        finally:
            self.is_countdown_active = False
    
    def _voice_recording_worker(self):
        """语音录制工作线程"""
        try:
            # 创建语音识别实例
            stt = SpeechToText(
                language_code='zh-CN',
                channels=1
            )
            
            # 开始录音识别（限制在voice_duration时间内）
            self.voice_text = stt.record_and_transcribe(duration=self.voice_duration)
            
        except Exception as e:
            self.voice_error = f"语音录制失败: {str(e)}"
            self.voice_text = None
        finally:
            self.is_voice_recording = False
    
    def _progress_display_worker(self):
        """进度显示工作线程"""
        start_time = time.time()
        
        while (self.is_countdown_active or self.is_voice_recording):
            elapsed = time.time() - start_time
            
            # 生成组合进度显示
            progress_text = self._generate_combined_progress(elapsed)
            self.context.oled_display.show_text_oled(progress_text)
            
            time.sleep(0.5)  # 0.5秒更新一次
        
        # 显示完成状态
        self.context.oled_display.show_text_oled(
            "拍照完成\n语音识别中...\n请稍候"
        )
    
    def _generate_combined_progress(self, elapsed: float) -> str:
        """生成组合进度显示"""
        # 拍照倒计时进度
        photo_remaining = max(0, self.photo_countdown - elapsed)
        photo_progress = min(elapsed / self.photo_countdown, 1.0)
        
        # 语音录制进度
        voice_progress = min(elapsed / self.voice_duration, 1.0) if STT_AVAILABLE else 0
        
        # 进度条（缩短以适应3行显示）
        bar_length = 6
        photo_filled = int(bar_length * photo_progress)
        voice_filled = int(bar_length * voice_progress)
        
        photo_bar = '#' * photo_filled + '-' * (bar_length - photo_filled)
        voice_bar = '#' * voice_filled + '-' * (bar_length - voice_filled) if STT_AVAILABLE else '------'
        
        # 组合显示（3行）
        display_text = f"拍照 {photo_remaining:.0f}s [{photo_bar}]\n"
        if STT_AVAILABLE:
            display_text += f"语音 [{voice_bar}]\n"
            display_text += "请摆pose并说话"
        else:
            display_text += "语音不可用\n"
            display_text += "请摆pose"
        
        return display_text
    
    def _stop_all_processes(self):
        """停止所有进程"""
        self.is_countdown_active = False
        self.is_voice_recording = False
    
    def validate_photo_voice_result(self, photo_success: bool, voice_text: Optional[str]) -> bool:
        """验证拍照+语音结果的有效性"""
        # 至少要有照片成功
        if not photo_success:
            return False
        
        # 语音是可选的，但如果有语音要验证其有效性
        if voice_text and len(voice_text.strip()) < 2:
            return False
            
        return True
    
    def get_fallback_voice_text(self) -> str:
        """获取语音录制失败时的备用文本"""
        fallback_texts = [
            "在拍照时感受到了当下的美好瞬间",
            "这个场景让我印象深刻",
            "在这里留下了特别的回忆",
            "感受到了这个地方的独特氛围",
            "这一刻很值得纪念"
        ]
        return fallback_texts[0] 