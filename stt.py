import sounddevice as sd
import numpy as np
import wave
import time
from google.cloud import speech
import os

# 设置参数
samplerate = 16000  # 采样率
channels = 1        # 单声道
duration = 5        # 录音时长（秒）
filename = "pyaudio.wav"

# 如果还没有设置环境变量，手动设置（替换成你的路径）
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/your/GOOGLE_STT_API.json"

# Step 1. 录音
print("准备录音，5秒钟...")
time.sleep(1)

recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=channels, dtype='int16')
sd.wait()  # 等待录音完成

print("录音完成，保存到文件...")

with wave.open(filename, mode='wb') as wf:
    wf.setnchannels(channels)
    wf.setsampwidth(2)  # 16bit = 2 bytes
    wf.setframerate(samplerate)
    wf.writeframes(recording.tobytes())

print(f"保存成功：{filename}")

# Step 2. 调用Google Speech-to-Text识别
print("上传到Google Speech-to-Text进行识别...")

client = speech.SpeechClient()

with open(filename, "rb") as audio_file:
    content = audio_file.read()

audio = speech.RecognitionAudio(content=content)

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="zh-CN",  # 如果是中文，改成 "zh"
)

response = client.recognize(config=config, audio=audio)

print("识别结果：")
for result in response.results:
    print("→", result.alternatives[0].transcript)