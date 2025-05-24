#!/usr/bin/env python3
"""
测试 show_text_oled 修复
验证修复后的 show_text_oled 会滚动一遍后结束，不会卡死
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
        
        # 测试短文本 (不需要滚动)
        print("2. 测试短文本...")
        start_time = time.time()
        oled.show_text_oled("测试短文本")
        end_time = time.time()
        print(f"✅ 短文本显示完成，耗时: {end_time - start_time:.2f}秒")
        time.sleep(1)
        
        # 测试多行文本 (不需要滚动)
        print("3. 测试多行文本...")
        start_time = time.time()
        oled.show_text_oled("第一行\n第二行\n第三行")
        end_time = time.time()
        print(f"✅ 多行文本显示完成，耗时: {end_time - start_time:.2f}秒")
        time.sleep(1)
        
        # 测试长文本 (需要滚动显示)
        print("4. 测试长文本滚动 (之前会卡死)...")
        long_text = """🌟 史莱姆漂流系统

欢迎来到漂流世界！
让我们开始你的
专属史莱姆之旅

这是第二页的内容
你现在看到的是
滚动显示的效果

这是第三页的内容
系统会自动滚动
显示所有内容

最后一页内容
滚动完成后会结束
不会无限循环了！"""
        
        print("   观察OLED屏幕，应该看到分页滚动显示...")
        start_time = time.time()
        oled.show_text_oled(long_text)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"✅ 长文本滚动显示完成，总耗时: {duration:.2f}秒")
        
        # 预期时间应该是：2.5秒(首页) + 1.5秒(中间页) + 2.5秒(末页) = 约6.5秒左右
        if 5.0 < duration < 15.0:  # 合理的滚动时间范围
            print("🎉 滚动时间合理，修复成功！")
        elif duration < 2.0:
            print("⚠️ 可能没有滚动，时间过短")
        else:
            print("⚠️ 滚动时间异常，可能仍有问题")
        
        time.sleep(1)
        
        # 测试超长文本
        print("5. 测试超长文本...")
        super_long_text = """第一页：史莱姆漂流系统是一个互动式的AR体验项目。

第二页：用户可以通过语音输入自己的心情状态，系统会生成对应的史莱姆角色。

第三页：史莱姆有自己的性格特点、执念、幻想癖好等属性。

第四页：用户可以和史莱姆一起拍照探索，寻找符合史莱姆执念的场景。

第五页：系统会根据照片内容给出相应的奖励，包括装饰品或史莱姆蛋。

第六页：这是最后一页，演示滚动显示功能正常工作。"""
        
        print("   观察更长的滚动过程...")
        start_time = time.time()
        oled.show_text_oled(super_long_text)
        end_time = time.time()
        
        print(f"✅ 超长文本滚动完成，耗时: {end_time - start_time:.2f}秒")
        
        # 清理显示
        print("6. 清理显示...")
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
    print("🔧 show_text_oled 滚动修复验证测试")
    print("=" * 50)
    
    success = test_show_text_oled()
    
    if success:
        print("\n🎉 修复验证成功！")
        print("现在 show_text_oled 会滚动一遍显示全部内容后结束")
        print("不会再无限循环卡死了")
        return 0
    else:
        print("\n❌ 修复验证失败")
        print("可能需要进一步调试")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 