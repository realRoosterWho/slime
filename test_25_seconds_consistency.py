#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试25秒语音录制一致性
验证初始语音输入和拍照+语音都使用25秒
"""

import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.voice_input_utils import VoiceInputManager
from core.components.photo_voice_utils import PhotoVoiceManager
from core.components.derive_context import DeriveContext

def test_25_seconds_consistency():
    """测试25秒录音时长一致性"""
    print("=== 测试25秒语音录制一致性 ===")
    
    try:
        # 创建上下文
        context = DeriveContext("测试文本")
        
        # 检查初始语音输入管理器
        voice_manager = VoiceInputManager(context)
        print(f"初始语音输入配置时长: {voice_manager.recording_config['duration']}秒")
        
        # 检查拍照+语音管理器
        photo_voice_manager = PhotoVoiceManager(context)
        print(f"拍照+语音录制时长: {photo_voice_manager.voice_duration}秒")
        
        # 验证一致性
        if (voice_manager.recording_config['duration'] == 25 and 
            photo_voice_manager.voice_duration == 25):
            print("✅ 一致性检查通过！所有语音录制都使用25秒")
            
            context.oled_display.show_text_oled(
                "25秒一致性\n检查通过\n初始和拍照+语音\n都是25秒"
            )
            
            return True
        else:
            print("❌ 一致性检查失败！")
            print(f"初始语音: {voice_manager.recording_config['duration']}秒")
            print(f"拍照+语音: {photo_voice_manager.voice_duration}秒")
            
            context.oled_display.show_text_oled(
                "一致性检查失败\n时长不匹配"
            )
            
            return False
            
    except Exception as e:
        print(f"测试异常: {e}")
        return False
    
    finally:
        # 清理资源
        try:
            if 'context' in locals():
                context.cleanup()
        except:
            pass

if __name__ == "__main__":
    success = test_25_seconds_consistency()
    sys.exit(0 if success else 1) 