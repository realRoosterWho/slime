import sounddevice as sd
import numpy as np
import wave
import time
from google.cloud import speech
import os
from typing import Optional

# 默认凭证路径
DEFAULT_CREDENTIALS_PATH = "/home/roosterwho/keys/nth-passage-458018-v2-d7658cf7d449.json"

class SpeechToText:
    def __init__(self, 
                 device_index: Optional[int] = None,
                 samplerate: int = 16000,
                 channels: int = 1,
                 language_code: str = "zh-CN",
                 credentials_path: Optional[str] = None):
        """
        初始化语音识别器
        
        Args:
            device_index: 麦克风设备索引，如果为None则使用默认设备
            samplerate: 采样率，默认16000Hz
            channels: 声道数，默认单声道
            language_code: 语言代码，默认中文
            credentials_path: Google Cloud凭证文件路径
        """
        self.device_index = device_index
        self.samplerate = samplerate
        self.channels = channels
        self.language_code = language_code
        
        # 检查并设置Google Cloud凭证
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        elif "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
            if os.path.exists(DEFAULT_CREDENTIALS_PATH):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = DEFAULT_CREDENTIALS_PATH
                print(f"⚠️ 使用默认凭证路径: {DEFAULT_CREDENTIALS_PATH}")
            else:
                raise EnvironmentError(
                    "未设置Google Cloud凭证。请通过以下方式之一设置：\n"
                    "1. 设置环境变量 GOOGLE_APPLICATION_CREDENTIALS\n"
                    "2. 在初始化时传入 credentials_path 参数\n"
                    "3. 确保默认凭证文件存在: " + DEFAULT_CREDENTIALS_PATH
                )
        
        # 初始化Google Speech客户端
        self.client = speech.SpeechClient()
        
        # 检查音频设备
        self._check_audio_device()
        
    def _check_audio_device(self):
        """检查音频设备配置"""
        try:
            # 获取设备信息
            if self.device_index is not None:
                device_info = sd.query_devices(self.device_index)
            else:
                device_info = sd.query_devices(kind='input')
            
            # 检查设备是否支持输入
            if device_info['max_input_channels'] == 0:
                raise ValueError(f"设备 {device_info['name']} 不支持输入")
            
            # 检查声道数是否支持
            if self.channels > device_info['max_input_channels']:
                print(f"⚠️ 警告: 设备 {device_info['name']} 只支持 {device_info['max_input_channels']} 个输入声道，"
                      f"将使用 {device_info['max_input_channels']} 个声道")
                self.channels = device_info['max_input_channels']
            
            # 检查采样率是否支持
            if self.samplerate > device_info['default_samplerate']:
                print(f"⚠️ 警告: 设备 {device_info['name']} 默认采样率为 {device_info['default_samplerate']}，"
                      f"将使用默认采样率")
                self.samplerate = int(device_info['default_samplerate'])
                
        except Exception as e:
            print("\n🔍 可用输入设备列表:")
            for i, dev in enumerate(sd.query_devices()):
                if dev['max_input_channels'] > 0:
                    print(f"  {i}: {dev['name']} (输入声道: {dev['max_input_channels']}, "
                          f"采样率: {dev['default_samplerate']})")
            raise ValueError(f"音频设备配置错误: {str(e)}\n请从上面的列表中选择一个有效的设备索引")
    
    def record(self, duration: int = 5, filename: str = "pyaudio.wav") -> np.ndarray:
        """
        录制音频
        
        Args:
            duration: 录音时长（秒）
            filename: 临时保存的文件名
            
        Returns:
            录制的音频数据
        """
        print(f"🎤 开始录音（{duration} 秒）...")
        
        try:
            # 录制音频
            recording = sd.rec(int(duration * self.samplerate),
                            samplerate=self.samplerate,
                            channels=self.channels,
                            dtype='int16',
                            device=self.device_index)
            sd.wait()
            
            # 保存为临时文件
            with wave.open(filename, mode='wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16bit = 2 bytes
                wf.setframerate(self.samplerate)
                wf.writeframes(recording.tobytes())
                
            print("✅ 录音完成")
            return recording
            
        except Exception as e:
            print("\n❌ 录音失败，请检查设备配置")
            print("🔍 可用输入设备列表:")
            for i, dev in enumerate(sd.query_devices()):
                if dev['max_input_channels'] > 0:
                    print(f"  {i}: {dev['name']} (输入声道: {dev['max_input_channels']}, "
                          f"采样率: {dev['default_samplerate']})")
            raise
    
    def transcribe(self, audio_data: Optional[np.ndarray] = None, filename: str = "pyaudio.wav") -> str:
        """
        将音频转换为文本
        
        Args:
            audio_data: 音频数据，如果为None则使用filename指定的文件
            filename: 音频文件名
            
        Returns:
            识别出的文本
        """
        print("🔍 正在识别语音...")
        
        # 如果提供了音频数据，先保存到文件
        if audio_data is not None:
            with wave.open(filename, mode='wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.samplerate)
                wf.writeframes(audio_data.tobytes())
        
        # 读取音频文件
        with open(filename, "rb") as audio_file:
            content = audio_file.read()
            
        # 配置识别参数
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.samplerate,
            language_code=self.language_code,
        )
        
        # 发送识别请求
        response = self.client.recognize(config=config, audio=audio)
        
        # 提取识别结果
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
            
        print(f"✅ 识别完成: {transcript}")
        return transcript
    
    def record_and_transcribe(self, duration: int = 5) -> str:
        """
        录制音频并直接转换为文本
        
        Args:
            duration: 录音时长（秒）
            
        Returns:
            识别出的文本
        """
        audio_data = self.record(duration)
        return self.transcribe(audio_data) 