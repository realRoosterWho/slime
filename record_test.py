#!/usr/bin/env python3

import sounddevice as sd
from scipy.io.wavfile import write

def find_input_device():
    print("\n🔍 正在查找可用输入设备...")
    for i, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0:
            print(f"✅ 可用输入设备: {dev['name']} → index={i}")
    return

find_input_device()

samplerate = 16000
duration = 5
channels = 1
filename = "mic_test.wav"

print("\n🎤 开始录音（5 秒）...")
recording = sd.rec(int(duration * samplerate),
                   samplerate=samplerate, channels=channels,
                   dtype='int16', device=1)
sd.wait()
write(filename, samplerate, recording)
print(f"✅ 已保存录音到 {filename}")