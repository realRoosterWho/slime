#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试菜单系统的GPIO清理修复
"""

import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_menu_cleanup():
    """测试菜单系统初始化和清理"""
    print("=== 测试菜单系统GPIO清理修复 ===")
    
    try:
        from core.menu.menu_manager import MenuSystem
        
        print("🚀 初始化菜单系统...")
        menu = MenuSystem()
        
        print("✅ 菜单系统初始化成功")
        print("🖼️ Logo应该已显示在LCD上")
        
        # 模拟运行一小段时间
        print("⏱️ 运行3秒后清理...")
        time.sleep(3)
        
        print("🧹 开始清理...")
        menu.cleanup()
        
        print("✅ 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_menu_cleanup() 