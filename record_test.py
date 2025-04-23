#!/usr/bin/env python3

import sounddevice as sd
from scipy.io.wavfile import write

def find_input_device():
    print("\n🔍 正在查找可用输入设备...")
    for i, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0:
            print(f"✅ 可用输入设备: {dev['name']} → index={i}")
            print(f"   采样率范围: {dev['default_samplerate']} Hz")
            print(f"   输入通道数: {dev['max_input_channels']}")
    return

find_input_device()

# 使用默认采样率
device_info = sd.query_devices(1, 'input')
samplerate = int(device_info['default_samplerate'])
duration = 5
channels = 1
filename = "mic_test.wav"

print(f"\n🎤 开始录音（5 秒，采样率: {samplerate} Hz）...")
recording = sd.rec(int(duration * samplerate),
                   samplerate=samplerate, channels=channels,
                   dtype='int16', device=1)
sd.wait()
write(filename, samplerate, recording)
print(f"✅ 已保存录音到 {filename}")