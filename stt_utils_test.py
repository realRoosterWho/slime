#!/usr/bin/env python3

from stt_utils import SpeechToText

def main():
    # 1. 基本使用（使用默认参数，包括单声道）
    print("\n=== 基本使用 ===")
    stt = SpeechToText()  # 默认使用单声道
    text = stt.record_and_transcribe(duration=5)
    print(f"识别结果: {text}")

    # 4. 使用不同的语言（保持单声道）
    print("\n=== 使用英文识别 ===")
    stt = SpeechToText(language_code="en-US", channels=1)  # 明确指定单声道
    text = stt.record_and_transcribe(duration=5)
    print(f"识别结果: {text}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}") 