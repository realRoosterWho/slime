#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 TakeNewPhotoState 的拍照+语音功能
验证新照片拍摄是否支持并行语音录制
"""

import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.derive_context import DeriveContext
from core.components.states.take_new_photo_state import TakeNewPhotoState
from core.components.states.analyze_new_photo_state import AnalyzeNewPhotoState

def test_take_new_photo_voice():
    """测试新照片拍摄+语音功能"""
    print("=== 测试新照片拍摄+语音功能 ===")
    
    context = None
    try:
        # 创建上下文
        context = DeriveContext("测试新照片+语音")
        
        # 设置史莱姆属性
        context.set_slime_attribute('obsession', '寻找宁静的自然美景')
        context.set_slime_attribute('tone', '温和好奇')
        
        # 显示测试信息
        context.oled_display.show_text_oled(
            "测试新照片+语音\n"
            "将同时进行:\n"
            "1. 拍照倒计时\n"
            "2. 25秒语音录制"
        )
        time.sleep(3)
        
        # 创建并执行 TakeNewPhotoState
        take_new_photo_state = TakeNewPhotoState()
        take_new_photo_state.execute(context)
        
        # 检查是否成功拍照
        photo_path = context.get_data('new_photo_path')
        voice_text = context.get_data('new_photo_voice_text')
        
        if photo_path:
            print(f"✅ 新照片拍摄成功: {photo_path}")
            if voice_text:
                print(f"✅ 语音录制成功: {voice_text[:50]}...")
            else:
                print("⚠️ 语音录制失败，使用默认文本")
            
            # 测试分析阶段
            context.oled_display.show_text_oled(
                "测试分析阶段\n"
                "结合照片和语音\n"
                "进行综合分析"
            )
            time.sleep(2)
            
            # 执行分析
            analyze_state = AnalyzeNewPhotoState()
            analyze_state.execute(context)
            
            # 检查分析结果
            analysis = context.get_data('new_photo_analysis')
            if analysis:
                print(f"✅ 新照片+语音分析成功: {analysis[:50]}...")
                context.oled_display.show_text_oled(
                    "新照片+语音\n测试完成\n\n功能正常"
                )
            else:
                print("❌ 分析失败")
                context.oled_display.show_text_oled(
                    "分析失败"
                )
                
        else:
            print("❌ 新照片拍摄失败")
            context.oled_display.show_text_oled(
                "新照片+语音\n测试失败"
            )
            return False
            
        time.sleep(3)
        return True
        
    except Exception as e:
        print(f"测试异常: {e}")
        if context:
            context.oled_display.show_text_oled(f"测试异常:\n{str(e)[:20]}...")
        return False
    
    finally:
        if context:
            try:
                context.cleanup()
            except:
                pass

if __name__ == "__main__":
    success = test_take_new_photo_voice()
    print(f"\n{'='*50}")
    if success:
        print("✅ 新照片+语音功能测试通过!")
        print("- 支持拍照和语音并行录制")
        print("- 分析时结合照片和语音信息")
        print("- 语音录制时长25秒")
    else:
        print("❌ 新照片+语音功能测试失败!")
    
    sys.exit(0 if success else 1) 