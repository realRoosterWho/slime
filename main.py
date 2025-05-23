import os
import sys
import signal

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.menu.menu_manager import MenuSystem

if __name__ == "__main__":
    try:
        menu = MenuSystem()
        print("菜单系统运行中...")
        print("使用上下摇杆选择，按钮1确认")
        print("按 Ctrl+C 退出")
        
        while menu.run_step():
            pass
            
        print("🧹 正在清理...")
        menu.cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"❌ 错误: {e}")
        if 'menu' in globals():
            try:
                menu.cleanup()
            except Exception:
                pass
        sys.exit(1) 