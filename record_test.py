import sounddevice as sd
from scipy.io.wavfile import write
import os

samplerate = 44100  # 采样率
duration = 5        # 录音时长（秒）
channels = 2        # 单声道
filename = "mic_test.wav"

print(f"🎤 开始录音（{duration} 秒）...")
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='int16', device=1)
sd.wait()

write(filename, samplerate, recording)
print(f"✅ 录音完成，保存为 {filename}")