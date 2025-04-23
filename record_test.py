#!/usr/bin/env python3

import sounddevice as sd
from scipy.io.wavfile import write

samplerate = 16000  # ✔️ 更通用
channels = 1        # ✔️ 建议用 1，除非你要立体声
device = 0          # 根据你之前的 query_devices

duration = 5
filename = "mic_test.wav"

print("🎤 正在录音中...")
recording = sd.rec(int(duration * samplerate), samplerate=samplerate,
                   channels=channels, dtype='int16', device=device)
sd.wait()

write(filename, samplerate, recording)
print(f"✅ 已保存到：{filename}")