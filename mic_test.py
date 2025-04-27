import sounddevice as sd
import numpy as np
import wave
import time

# 设置参数
samplerate = 16000  # 采样率
channels = 1        # 单声道（虽然I2S是双声道，但通常我们用单声道提取）
duration = 5        # 录音时长（秒）
filename = "test.wav"

print("准备录音，5秒钟...")
time.sleep(1)

# 开始录音
recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=channels, dtype='int16')
sd.wait()  # 等待录音完成

print("录音完成，保存文件中...")

# 保存为 WAV 文件
with wave.open(filename, mode='wb') as wf:
    wf.setnchannels(channels)
    wf.setsampwidth(2)  # 16位 int16 = 2字节
    wf.setframerate(samplerate)
    wf.writeframes(recording.tobytes())

print(f"保存成功：{filename}")