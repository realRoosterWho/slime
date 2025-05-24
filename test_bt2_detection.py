#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试BT2按键检测功能
"""

import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.derive_context import DeriveContext

def test_bt2_detection():
    """测试BT2检测功能"""
    print("=== 测试BT2按键检测功能 ===")
    
    try:
        # 创建上下文
        context = DeriveContext("测试文本")
        context.logger.log_step("测试开始", "测试BT2按键检测")
        
        print("显示测试界面，请按BT1或BT2测试...")
        print("BT1 - 确认")
        print("BT2 - 重录/默认")
        print("长按任意键 - 返回菜单")
        
        # 测试按键检测
        result = context.oled_display.wait_for_button_with_text(
            context.controller,
            "按键检测测试\n\n按BT1 - 确认\n按BT2 - 重录\n长按 - 返回菜单",
            context=context
        )
        
        # 显示检测结果
        if result == 2:
            print("检测到长按返回菜单")
            message = "检测到长按\n返回菜单"
        elif hasattr(context.controller, 'last_button'):
            if context.controller.last_button == 'BTN1':
                print("检测到BT1按下")
                message = "检测到BT1\n确认操作"
            elif context.controller.last_button == 'BTN2':
                print("检测到BT2按下 - 重录功能！")
                message = "检测到BT2\n重录功能"
            else:
                print(f"检测到未知按键: {context.controller.last_button}")
                message = f"未知按键\n{context.controller.last_button}"
        else:
            print("未检测到按键信息")
            message = "未检测到\n按键信息"
        
        # 显示结果
        context.oled_display.show_text_oled(message)
        time.sleep(3)
        
        context.logger.log_step("测试完成", f"按键检测结果: {context.controller.last_button if hasattr(context.controller, 'last_button') else 'None'}")
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
        return 42
        
    except Exception as e:
        print(f"测试异常: {e}")
        return 1
    
    finally:
        # 清理资源
        try:
            if 'context' in locals():
                context.cleanup()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    exit_code = test_bt2_detection()
    sys.exit(exit_code) 