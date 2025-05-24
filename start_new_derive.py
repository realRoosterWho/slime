#!/usr/bin/env python3
"""
史莱姆漂流新架构启动脚本

使用优化后的状态机架构启动史莱姆漂流系统
"""

import os
import sys
import signal
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def cleanup_handler(signum, frame):
    """清理资源并优雅退出"""
    print("\n🛑 检测到中断信号，正在清理资源...")
    try:
        # 清理全局资源管理器
        from core.components.performance_optimizer import global_resource_manager
        global_resource_manager.release_all()
        
        # 如果存在state_machine实例，保存日志并清理
        if 'state_machine' in globals():
            state_machine.context.cleanup()
            print("✅ 状态机已清理")
        
        print("✅ 已清理资源")
    except Exception as e:
        print(f"清理过程中出错: {e}")
    finally:
        sys.exit(0)

def get_initial_text_from_user():
    """获取用户输入的初始文本（现在通过语音输入状态处理）"""
    # 注意：这个函数现在仅作为备用，实际的文本获取通过语音输入状态完成
    # 这里返回None，表示需要通过语音输入状态获取
    return None

def main():
    """主函数"""
    print("🌟 史莱姆漂流系统 - 新架构版本")
    print("=" * 50)
    
    # 设置信号处理
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        # 导入新架构组件
        print("📦 加载系统组件...")
        from core.components.derive_state_machine import DeriveStateMachine
        from core.components.derive_context import DeriveContext
        from core.components.performance_optimizer import global_optimizer
        
        print("✅ 组件加载成功")
        
        # 获取初始文本（现在通过语音输入状态处理）
        initial_text = get_initial_text_from_user()
        if initial_text:
            print(f"📝 备用文本: {initial_text[:50]}...")
        else:
            print("🎤 将通过语音输入获取用户心情")
        
        # 创建并运行状态机
        print("🚀 启动状态机...")
        state_machine = DeriveStateMachine(initial_text)  # 可以传入None
        
        # 初始化状态机
        print("⚙️  初始化状态...")
        state_machine.initialize_states()
        
        # 运行状态机
        print("🎮 开始漂流旅程...")
        return_to_menu = state_machine.run()
        
        # 根据返回值决定退出方式
        if return_to_menu:
            print("🔄 用户请求返回菜单")
            sys.exit(42)  # 特殊退出码表示返回菜单
        else:
            print("✨ 漂流旅程结束")
            sys.exit(0)   # 正常退出
            
    except KeyboardInterrupt:
        print("\n⏹️  用户中断程序")
        sys.exit(42)  # 返回菜单
        
    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
        
        # 打印详细错误信息（调试用）
        import traceback
        print("\n🔍 详细错误信息:")
        traceback.print_exc()
        
        # 尝试清理资源
        try:
            if 'state_machine' in locals():
                state_machine.context.cleanup()
        except Exception:
            pass
        
        print("\n💡 建议:")
        print("1. 检查硬件连接是否正常")
        print("2. 确认网络连接是否稳定")
        print("3. 检查API密钥配置")
        print("4. 检查语音识别模块是否可用")
        print("5. 查看完整日志了解详细错误")
        
        sys.exit(1)  # 错误退出
        
    finally:
        # 最终清理
        try:
            from core.components.performance_optimizer import global_resource_manager
            global_resource_manager.release_all()
        except Exception:
            pass

if __name__ == "__main__":
    main() 