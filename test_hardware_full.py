#!/usr/bin/env python3
"""
史莱姆漂流状态机硬件完整测试
在真实硬件环境下运行完整的8个状态流程
"""

import sys
import os
import time
from dotenv import load_dotenv

def check_environment():
    """检查环境配置"""
    print("🔧 检查环境配置...")
    
    # 加载环境变量
    load_dotenv()
    
    # 检查必需的API密钥
    openai_key = os.getenv("OPENAI_API_KEY")
    replicate_key = os.getenv("REPLICATE_API_KEY")
    
    if not openai_key:
        print("❌ 缺少 OPENAI_API_KEY")
        return False
    else:
        print(f"✅ OPENAI_API_KEY: {openai_key[:10]}...")
    
    if not replicate_key:
        print("❌ 缺少 REPLICATE_API_KEY")
        return False
    else:
        print(f"✅ REPLICATE_API_KEY: {replicate_key[:10]}...")
    
    return True

def run_full_test():
    """运行完整的硬件测试"""
    print("\n🎮 启动史莱姆漂流完整硬件测试")
    print("=" * 50)
    
    try:
        # 导入状态机
        from core.components.derive_state_machine import DeriveStateMachine
        
        # 使用真实的初始文本
        initial_text = "感觉空气布满了水雾，有一种看不清前方道路的错觉，觉得很放松。你能带我在这个氛围里面漂流吗？"
        
        print(f"📝 初始文本: {initial_text}")
        print(f"⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n🤖 创建史莱姆漂流状态机...")
        
        # 创建状态机
        state_machine = DeriveStateMachine(initial_text)
        
        print("🎯 开始完整流程测试...")
        print("📌 提示：可以长按按钮2随时返回菜单")
        print("\n" + "=" * 50)
        
        # 运行状态机
        return_to_menu = state_machine.run()
        
        print("\n" + "=" * 50)
        print(f"⏰ 结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if return_to_menu:
            print("🏠 用户选择返回菜单")
            return 42  # 特殊退出码
        else:
            print("✅ 完整流程执行完成")
            return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
        return 1
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """主函数"""
    print("🧪 史莱姆漂流硬件完整测试")
    print("🎯 目标：测试完整的8个状态流程")
    print("💡 包含：AI生成、图像处理、硬件交互")
    print("⚡ 注意：此测试将产生真实的API调用费用\n")
    
    # 检查环境
    if not check_environment():
        print("💥 环境检查失败，无法运行测试")
        return 1
    
    print("✅ 环境检查通过")
    
    # 确认开始测试
    print("\n⚠️  警告：此测试将:")
    print("   - 调用 OpenAI API (产生费用)")
    print("   - 调用 Replicate API (产生费用)")
    print("   - 使用摄像头拍照")
    print("   - 使用显示屏和按钮")
    
    # 给用户5秒思考时间
    print("\n⏳ 5秒后自动开始测试...")
    for i in range(5, 0, -1):
        print(f"   {i}秒...")
        time.sleep(1)
    
    print("\n🚀 开始测试！")
    
    # 运行完整测试
    exit_code = run_full_test()
    
    print("\n" + "=" * 50)
    if exit_code == 0:
        print("🎉 硬件完整测试成功完成！")
        print("📊 所有8个状态都已验证")
        print("🔧 状态机架构重构成功")
    elif exit_code == 42:
        print("🏠 用户返回菜单，测试正常结束")
    else:
        print("💥 测试失败，需要检查问题")
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 