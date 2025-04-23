#!/usr/bin/env python3

import sounddevice as sd
from scipy.io.wavfile import write

print(sd.query_devices(0, 'input'))

samplerate = 16000
duration = 5
channels = 1
filename = "mic_test.wav"

print("🎤 开始录音（5 秒）...")
recording = sd.rec(int(duration * samplerate),
                   samplerate=samplerate, channels=channels,
                   dtype='int16', device=0)
sd.wait()
write(filename, samplerate, recording)
print(f"✅ 已保存录音到 {filename}")