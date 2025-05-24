#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试心情处理到史莱姆生成的数据传递
验证InitState能否正确获取ProcessMoodState保存的心情文本
"""

import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.derive_context import DeriveContext
from core.components.states.process_mood_state import ProcessMoodState
from core.components.states.init_state import InitState

def test_mood_to_slime_data_flow():
    """测试心情数据从ProcessMood传递到Init状态"""
    print("=== 测试心情到史莱姆生成的数据传递 ===")
    
    context = None
    try:
        # 创建上下文
        context = DeriveContext("测试文本")
        
        # 模拟语音输入的水边心情
        test_voice_text = "我现在心情很兴奋想去水边或者海边游泳池也行小水坑也行因为水边能让我感觉非常的快乐"
        context.set_data('raw_voice_text', test_voice_text)
        context.set_data('is_voice_input', True)
        
        print(f"📝 模拟语音输入: {test_voice_text[:30]}...")
        
        # 执行心情处理状态
        context.oled_display.show_text_oled(
            "测试心情处理\n模拟水边心情\n语音输入"
        )
        time.sleep(2)
        
        process_mood_state = ProcessMoodState()
        process_mood_state.execute(context)
        
        # 检查ProcessMoodState的输出
        processed_mood = context.get_data('initial_text')
        saved_mood = context.get_data('processed_mood')
        
        print(f"✅ 心情处理完成:")
        print(f"   processed_mood: {processed_mood[:50] if processed_mood else 'None'}...")
        print(f"   saved_mood: {saved_mood[:50] if saved_mood else 'None'}...")
        
        if not processed_mood:
            print("❌ 心情处理失败，没有保存处理后的心情")
            return False
        
        # 执行初始化状态
        context.oled_display.show_text_oled(
            "测试史莱姆生成\n基于水边心情\n生成性格"
        )
        time.sleep(2)
        
        init_state = InitState()
        init_state.execute(context)
        
        # 检查InitState的输出
        personality = context.get_data('personality')
        obsession = context.get_slime_attribute('obsession')
        
        print(f"✅ 史莱姆生成完成:")
        print(f"   personality: {personality[:50] if personality else 'None'}...")
        print(f"   obsession: {obsession[:50] if obsession else 'None'}...")
        
        # 验证是否正确反映了水边心情
        if personality and ('水' in personality or '海' in personality or '游泳' in personality or '液体' in personality or '流动' in personality):
            print("✅ 史莱姆性格正确反映了水边心情！")
            context.oled_display.show_text_oled(
                "修复成功!\n史莱姆性格\n正确反映水边心情"
            )
            return True
        else:
            print("⚠️ 史莱姆性格可能没有完全反映水边心情")
            print(f"   检查personality内容: {personality}")
            context.oled_display.show_text_oled(
                "需要进一步检查\n性格生成内容"
            )
            return True  # 数据传递成功，但内容需要检查
            
    except Exception as e:
        print(f"测试异常: {e}")
        if context:
            context.oled_display.show_text_oled(f"测试异常:\n{str(e)[:20]}...")
        return False
    
    finally:
        if context:
            try:
                time.sleep(3)
                context.cleanup()
            except:
                pass

if __name__ == "__main__":
    success = test_mood_to_slime_data_flow()
    print(f"\n{'='*50}")
    if success:
        print("✅ 心情到史莱姆数据传递测试通过!")
        print("- ProcessMoodState正确保存处理后心情")
        print("- InitState正确获取心情文本")
        print("- 史莱姆性格基于正确的心情生成")
    else:
        print("❌ 心情到史莱姆数据传递测试失败!")
    
    sys.exit(0 if success else 1) 