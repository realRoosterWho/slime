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
    """拍照+语音录制管理器 - 处理拍照脚本和并行语音录制（25秒）"""
    
    def __init__(self, context):
        self.context = context
        self.is_countdown_active = False
        self.is_voice_recording = False
        self.camera_thread = None
        self.progress_thread = None
        
        # 录制配置
        self.voice_duration = 25   # 语音录制25秒（测试用，更充足的时间）
        
        # 结果存储
        self.photo_taken = False
        self.voice_text = None
        self.voice_error = None
        
    def take_photo_with_voice(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        执行拍照脚本 + 并行语音录制（25秒）
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (拍照成功, 语音文本, 错误信息)
        """
        try:
            self.context.logger.log_step("拍照+语音", "开始拍照脚本和25秒语音录制")
            
            # 重置状态
            self._reset_state()
            
            # 显示准备界面
            self._show_preparation()
            
            # 等待用户确认开始
            result = self.context.oled_display.wait_for_button_with_text(
                self.context.controller,
                "拍照+语音模式\n\n同时进行拍照倒计时\n和语音录制\n\nBT1开始",
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
            "拍照+语音模式\n准备拍摄\n并描述感受"
        )
        time.sleep(2)
    
    def _start_photo_voice_process(self) -> bool:
        """启动拍照脚本和语音录制 - 录音在主线程"""
        try:
            # 启动拍照脚本线程（并行执行）
            self.camera_thread = threading.Thread(
                target=self._camera_script_worker
            )
            
            # 显示开始提示
            self.context.oled_display.show_text_oled("即将开始\n对准周围环境+说话...")
            time.sleep(1)
            
            # 先启动拍照脚本
            self.is_countdown_active = True
            self.camera_thread.start()
            
            # 主线程执行语音录制（如果可用）
            if STT_AVAILABLE:
                self.is_voice_recording = True
                success = self._record_voice_in_main_thread()
            else:
                success = True
                # 如果没有语音功能，等待拍照完成
                self.camera_thread.join()
            
            # 等待拍照线程完成（如果还没完成）
            if self.camera_thread.is_alive():
                self.camera_thread.join()
            
            return self.photo_taken and success
            
        except Exception as e:
            self.voice_error = f"拍照+语音过程异常: {str(e)}"
            self._stop_all_processes()
            return False
    
    def _record_voice_in_main_thread(self) -> bool:
        """在主线程中执行语音录制"""
        try:
            self.context.logger.log_step("语音录制", "在主线程开始25秒语音录制")
            
            # 创建语音识别实例
            stt = SpeechToText(
                language_code='zh-CN',
                channels=1
            )
            
            # 在主线程中执行录音，同时显示进度
            start_time = time.time()
            
            # 启动进度显示子线程
            self.progress_thread = threading.Thread(
                target=self._progress_display_worker,
                args=(start_time,)
            )
            self.progress_thread.start()
            
            # 主线程执行录音（阻塞）
            self.voice_text = stt.record_and_transcribe(duration=self.voice_duration)
            
            # 录音完成，停止进度显示
            self.is_voice_recording = False
            
            # 等待进度显示线程结束
            if self.progress_thread.is_alive():
                self.progress_thread.join()
            
            # 显示完成状态
            self.context.oled_display.show_text_oled(
                "语音录制完成\n等待拍照完成...\n请稍候"
            )
            
            self.context.logger.log_step("语音录制完成", f"录制到文本: {self.voice_text[:30] if self.voice_text else 'None'}...")
            return True
            
        except Exception as e:
            self.voice_error = f"语音录制失败: {str(e)}"
            self.voice_text = None
            self.is_voice_recording = False
            self.context.logger.log_step("语音录制失败", str(e))
            return False
    
    def _camera_script_worker(self):
        """拍照脚本工作线程 - 直接启动camera脚本"""
        try:
            self.context.logger.log_step("拍照脚本", "启动run camera脚本")
            # 直接调用camera脚本，让脚本自己处理倒计时和拍照
            run_camera_test()
            self.photo_taken = True
            self.context.logger.log_step("拍照完成", "camera脚本执行完成")
                
        except Exception as e:
            self.voice_error = f"拍照脚本失败: {str(e)}"
            self.photo_taken = False
            self.context.logger.log_step("拍照失败", str(e))
        finally:
            self.is_countdown_active = False
    
    def _progress_display_worker(self, start_time: float):
        """进度显示工作线程 - 显示语音录制进度"""
        while self.is_voice_recording:
            elapsed = time.time() - start_time
            
            # 生成语音录制进度显示
            progress_text = self._generate_voice_progress(elapsed)
            self.context.oled_display.show_text_oled(progress_text)
            
            time.sleep(0.5)  # 0.5秒更新一次
    
    def _generate_voice_progress(self, elapsed: float) -> str:
        """生成语音录制进度显示"""
        # 语音录制进度
        voice_progress = min(elapsed / self.voice_duration, 1.0) if STT_AVAILABLE else 0
        remaining_time = max(0, self.voice_duration - elapsed)
        
        # 进度条
        bar_length = 8
        voice_filled = int(bar_length * voice_progress)
        voice_bar = '#' * voice_filled + '-' * (bar_length - voice_filled)
        percentage = int(voice_progress * 100)
        
        # 简化显示（3行）
        if STT_AVAILABLE:
            display_text = f"语音录制中\n"
            display_text += f"[{voice_bar}] {percentage}%\n"
            display_text += f"剩余 {remaining_time:.0f} 秒"
        else:
            display_text = "拍照模式\n"
            display_text += "语音功能不可用\n"
            display_text += "仅拍照"
        
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