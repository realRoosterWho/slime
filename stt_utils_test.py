#!/usr/bin/env python3

from stt_utils import SpeechToText

def main():
    # 1. 基本使用
    print("\n=== 基本使用 ===")
    stt = SpeechToText()
    text = stt.record_and_transcribe(duration=5)
    print(f"识别结果: {text}")

    # 2. 使用特定麦克风设备
    print("\n=== 使用特定麦克风设备 ===")
    stt = SpeechToText(device_index=1)  # 使用索引为1的麦克风
    text = stt.record_and_transcribe(duration=5)
    print(f"识别结果: {text}")

    # 3. 分步录音和识别
    print("\n=== 分步录音和识别 ===")
    stt = SpeechToText()
    # 先录音
    audio_data = stt.record(duration=5)
    # 再识别
    text = stt.transcribe(audio_data)
    print(f"识别结果: {text}")

    # 4. 使用不同的语言
    print("\n=== 使用英文识别 ===")
    stt = SpeechToText(language_code="en-US")
    text = stt.record_and_transcribe(duration=5)
    print(f"识别结果: {text}")

    # 5. 使用自定义凭证路径
    print("\n=== 使用自定义凭证路径 ===")
    stt = SpeechToText(
        credentials_path="/path/to/your/credentials.json"  # 替换为你的凭证路径
    )
    text = stt.record_and_transcribe(duration=5)
    print(f"识别结果: {text}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}") 