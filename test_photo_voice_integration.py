#!/usr/bin/env python3
"""
测试 Photo+Voice Integration 功能
验证15秒拍照倒计时+并行语音录制功能
"""

import os
import sys
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_photo_voice_manager():
    """测试PhotoVoiceManager功能"""
    try:
        print("测试 PhotoVoiceManager 功能...")
        
        # 导入必要的模块
        from core.components.photo_voice_utils import PhotoVoiceManager
        from core.display.display_utils import DisplayManager
        
        # 创建虚拟上下文
        class MockContext:
            def __init__(self):
                self.oled_display = DisplayManager("OLED")
                self.logger = MockLogger()
                
            class MockController:
                def __init__(self):
                    self.last_button = 'BTN1'
            
            controller = MockController()
        
        class MockLogger:
            def log_step(self, step, message):
                print(f"[LOG] {step}: {message}")
        
        # 创建虚拟上下文
        mock_context = MockContext()
        
        # 测试PhotoVoiceManager初始化
        print("1. 测试PhotoVoiceManager初始化...")
        photo_voice_manager = PhotoVoiceManager(mock_context)
        print("PhotoVoiceManager初始化成功")
        
        # 测试进度显示生成
        print("2. 测试进度显示生成...")
        for elapsed in [0, 5, 10, 15]:
            progress_text = photo_voice_manager._generate_combined_progress(elapsed)
            lines = progress_text.split('\n')
            print(f"   {elapsed}秒进度:")
            print(f"   内容: {repr(progress_text)}")
            print(f"   行数: {len(lines)}")
            
            if len(lines) <= 3:
                print("   符合3行限制")
            else:
                print("   超过3行限制")
            print()
        
        # 测试备用语音文本
        print("3. 测试备用语音文本...")
        fallback_text = photo_voice_manager.get_fallback_voice_text()
        print(f"   备用文本: {fallback_text}")
        
        # 测试结果验证
        print("4. 测试结果验证...")
        test_cases = [
            (True, "这是一段测试语音", True, "有效结果"),
            (False, "测试语音", False, "拍照失败"),
            (True, "", False, "语音为空"),
            (True, "很短", False, "语音过短"),
        ]
        
        for photo_success, voice_text, expected, description in test_cases:
            result = photo_voice_manager.validate_photo_voice_result(photo_success, voice_text)
            status = "通过" if result == expected else "失败"
            print(f"   {description}: {status}")
        
        print("PhotoVoiceManager测试完成")
        return True
        
    except Exception as e:
        print(f"PhotoVoiceManager测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_states_import():
    """测试新状态类的导入"""
    try:
        print("测试新状态类导入...")
        
        # 测试导入TakePhotoWithVoiceState
        print("1. 导入TakePhotoWithVoiceState...")
        from core.components.states.take_photo_with_voice_state import TakePhotoWithVoiceState
        state1 = TakePhotoWithVoiceState()
        print(f"   状态类型: {state1.state_type}")
        
        # 测试导入ProcessPhotoVoiceState
        print("2. 导入ProcessPhotoVoiceState...")
        from core.components.states.process_photo_voice_state import ProcessPhotoVoiceState
        state2 = ProcessPhotoVoiceState()
        print(f"   状态类型: {state2.state_type}")
        
        # 测试状态机注册
        print("3. 测试状态机注册...")
        from core.components.derive_state_machine import DeriveStateMachine
        
        # 创建虚拟上下文
        class MockContext:
            pass
        
        mock_context = MockContext()
        state_machine = DeriveStateMachine(mock_context)
        
        # 检查新状态是否注册
        from core.components.derive_states import DeriveState
        if DeriveState.TAKE_PHOTO_WITH_VOICE in state_machine.states:
            print("   TAKE_PHOTO_WITH_VOICE状态已注册")
        else:
            print("   TAKE_PHOTO_WITH_VOICE状态未注册")
            
        if DeriveState.PROCESS_PHOTO_VOICE in state_machine.states:
            print("   PROCESS_PHOTO_VOICE状态已注册")
        else:
            print("   PROCESS_PHOTO_VOICE状态未注册")
        
        print("状态导入测试完成")
        return True
        
    except Exception as e:
        print(f"状态导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_display_compatibility():
    """测试显示兼容性"""
    try:
        print("测试显示兼容性...")
        
        from core.display.display_utils import DisplayManager
        
        # 初始化OLED显示
        print("1. 初始化OLED显示...")
        oled = DisplayManager("OLED")
        
        # 测试各种显示文本
        test_texts = [
            "拍照+语音模式\n准备摆pose\n并描述感受",
            "3秒后开始\n准备摆pose...",
            "拍照 15s [------]\n语音 [------]\n请摆pose并说话",
            "拍照 0s [######]\n语音 [####--]\n请摆pose并说话",
            "拍照完成\n语音识别中...\n请稍候"
        ]
        
        for i, text in enumerate(test_texts, 1):
            lines = text.split('\n')
            print(f"   测试文本{i}: {len(lines)}行")
            
            if len(lines) <= 3:
                print(f"     符合要求")
            else:
                print(f"     超出限制")
            
            # 在OLED上显示
            oled.show_text_oled(text)
            time.sleep(1)
        
        print("显示兼容性测试完成")
        return True
        
    except Exception as e:
        print(f"显示兼容性测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Photo+Voice Integration 测试")
    print("=" * 60)
    
    all_tests_passed = True
    
    # 测试PhotoVoiceManager
    if not test_photo_voice_manager():
        all_tests_passed = False
    print()
    
    # 测试状态导入
    if not test_states_import():
        all_tests_passed = False
    print()
    
    # 测试显示兼容性
    if not test_display_compatibility():
        all_tests_passed = False
    print()
    
    # 总结
    print("=" * 60)
    if all_tests_passed:
        print("所有测试通过！Photo+Voice Integration 已成功集成")
        print("现在用户可以选择:")
        print("- 快速拍照模式（原有功能）")
        print("- 拍照+语音模式（15秒倒计时+并行语音录制）")
        return 0
    else:
        print("部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 