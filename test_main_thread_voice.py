#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试录音在主线程的新拍照+语音架构
"""

import sys
import os
import time
import threading

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.derive_context import DeriveContext
from core.components.photo_voice_utils import PhotoVoiceManager

def test_main_thread_voice():
    """测试录音在主线程的架构"""
    print("=== 测试录音在主线程的拍照+语音架构 ===")
    print(f"当前线程: {threading.current_thread().name}")
    
    try:
        # 创建上下文
        context = DeriveContext("测试文本")
        context.logger.log_step("测试开始", "测试录音在主线程的架构")
        
        # 创建拍照+语音管理器
        photo_voice_manager = PhotoVoiceManager(context)
        
        print("架构说明:")
        print("- 主线程：执行语音录制（阻塞）")
        print("- 子线程：启动camera脚本")
        print("- 子线程：显示进度")
        print("开始测试...")
        
        # 测试拍照+语音
        success, voice_text, error = photo_voice_manager.take_photo_with_voice()
        
        # 显示结果
        if success:
            print(f"拍照+语音成功!")
            print(f"语音文本: {voice_text if voice_text else '无语音录制'}")
            
            context.oled_display.show_text_oled(
                f"测试成功\n"
                f"录音在主线程\n"
                f"架构工作正常"
            )
        else:
            print(f"拍照+语音失败: {error}")
            context.oled_display.show_text_oled(
                f"测试失败\n{error}"
            )
        
        time.sleep(3)
        context.logger.log_step("测试完成", f"结果: {'成功' if success else '失败'}")
        
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
    exit_code = test_main_thread_voice()
    sys.exit(exit_code) 