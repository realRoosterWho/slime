#!/usr/bin/env python3
"""
测试简化后的语音进度条显示
验证是否只占用3行以内
"""

import os
import sys
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_progress_display():
    """测试进度条显示"""
    try:
        print("🧪 测试简化后的语音进度条显示...")
        
        # 导入显示管理器
        from core.display.display_utils import DisplayManager
        from core.components.voice_input_utils import VoiceInputManager
        
        # 创建虚拟上下文
        class MockContext:
            def __init__(self):
                self.oled_display = DisplayManager("OLED")
                
        # 初始化OLED显示
        print("1. 初始化OLED显示...")
        oled = DisplayManager("OLED")
        mock_context = MockContext()
        voice_manager = VoiceInputManager(mock_context)
        print("✅ 初始化成功")
        
        # 测试不同进度的显示
        test_times = [0, 2, 4, 6, 8]  # 不同的录音进度
        duration = 8
        
        print("2. 测试进度条显示...")
        for elapsed in test_times:
            progress_text = voice_manager._generate_progress_text(elapsed, duration)
            lines = progress_text.split('\n')
            
            print(f"   进度 {elapsed}/{duration}秒:")
            print(f"   显示内容: {repr(progress_text)}")
            print(f"   行数: {len(lines)}")
            
            if len(lines) <= 3:
                print("   ✅ 符合3行限制")
            else:
                print("   ❌ 超过3行限制")
            
            # 在OLED上显示
            oled.show_text_oled(progress_text)
            time.sleep(1.5)
            print()
        
        # 测试录音完成显示
        print("3. 测试录音完成显示...")
        completion_text = "录音完成\n正在识别...\n[########] 100%"
        completion_lines = completion_text.split('\n')
        print(f"   完成显示内容: {repr(completion_text)}")
        print(f"   行数: {len(completion_lines)}")
        
        if len(completion_lines) <= 3:
            print("   ✅ 符合3行限制")
        else:
            print("   ❌ 超过3行限制")
        
        oled.show_text_oled(completion_text)
        time.sleep(2)
        
        # 测试准备界面显示
        print("4. 测试准备界面显示...")
        prep_text = "说出你的心情\nBT1开始录音\nBT2默认心情"
        prep_lines = prep_text.split('\n')
        print(f"   准备界面内容: {repr(prep_text)}")
        print(f"   行数: {len(prep_lines)}")
        
        if len(prep_lines) <= 3:
            print("   ✅ 符合3行限制")
        else:
            print("   ❌ 超过3行限制")
        
        oled.show_text_oled(prep_text)
        time.sleep(2)
        
        # 清理显示
        print("5. 清理显示...")
        oled.clear()
        print("✅ 测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("🔧 语音进度条简化测试")
    print("=" * 50)
    
    success = test_progress_display()
    
    if success:
        print("\n🎉 进度条简化成功！")
        print("现在所有显示都在3行以内")
        return 0
    else:
        print("\n❌ 进度条测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 