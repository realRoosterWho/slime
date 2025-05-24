#!/usr/bin/env python3
"""
测试 show_text_oled 修复
验证修复后的 show_text_oled 不会卡死
"""

import os
import sys
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_show_text_oled():
    """测试修复后的 show_text_oled 方法"""
    try:
        print("🧪 测试 show_text_oled 修复...")
        
        # 导入显示管理器
        from core.display.display_utils import DisplayManager
        
        # 初始化OLED显示
        print("1. 初始化OLED显示...")
        oled = DisplayManager("OLED")
        print("✅ OLED初始化成功")
        
        # 测试短文本 (不应该卡死)
        print("2. 测试短文本...")
        oled.show_text_oled("测试短文本")
        print("✅ 短文本显示完成")
        time.sleep(1)
        
        # 测试多行文本 (不应该卡死)
        print("3. 测试多行文本...")
        oled.show_text_oled("第一行\n第二行\n第三行")
        print("✅ 多行文本显示完成")
        time.sleep(1)
        
        # 测试长文本 (之前会卡死的场景)
        print("4. 测试长文本 (之前会卡死)...")
        long_text = """🌟 史莱姆漂流系统

欢迎来到漂流世界！
让我们开始你的
专属史莱姆之旅

这是一段很长的文本
用来测试之前会导致卡死的情况
现在应该不会卡死了
而是显示前几行并用省略号表示"""
        
        start_time = time.time()
        oled.show_text_oled(long_text)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"✅ 长文本显示完成，耗时: {duration:.2f}秒")
        
        if duration < 2.0:  # 如果在2秒内完成，说明没有卡死
            print("🎉 修复成功！show_text_oled 不再卡死")
        else:
            print("⚠️ 可能仍有问题，耗时过长")
        
        time.sleep(1)
        
        # 清理显示
        print("5. 清理显示...")
        oled.clear()
        print("✅ 清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("🔧 show_text_oled 修复验证测试")
    print("=" * 50)
    
    success = test_show_text_oled()
    
    if success:
        print("\n🎉 修复验证成功！")
        print("现在可以安全使用 show_text_oled 方法")
        return 0
    else:
        print("\n❌ 修复验证失败")
        print("可能需要进一步调试")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 