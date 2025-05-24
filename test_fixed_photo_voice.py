#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试修复后的拍照+语音功能
验证真正的同时拍照和录音
"""

import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.derive_context import DeriveContext
from core.components.photo_voice_utils import PhotoVoiceManager

def test_photo_voice_timing():
    """测试拍照+语音时序"""
    print("=== 测试拍照+语音时序 ===")
    
    try:
        # 创建上下文
        context = DeriveContext("测试文本")
        context.logger.log_step("测试开始", "测试拍照+语音时序")
        
        # 创建拍照+语音管理器
        photo_voice_manager = PhotoVoiceManager(context)
        
        print("拍照+语音管理器初始化成功")
        print(f"相机可用: {photo_voice_manager.camera_manager is not None}")
        print(f"语音可用: {photo_voice_manager.voice_text is not None or 'STT_AVAILABLE' in globals()}")
        
        print("\n开始拍照+语音流程...")
        print("- 15秒拍照倒计时")
        print("- 12秒并行语音录制")
        print("- 相机预先启动，倒计时结束立即拍照")
        
        # 开始测试
        start_time = time.time()
        
        # 执行拍照+语音
        photo_success, voice_text, error_msg = photo_voice_manager.take_photo_with_voice()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n测试结果:")
        print(f"- 总耗时: {total_time:.1f} 秒")
        print(f"- 拍照成功: {photo_success}")
        print(f"- 语音文本: {voice_text[:50] if voice_text else 'None'}...")
        print(f"- 错误信息: {error_msg or 'None'}")
        
        # 检查时序
        if total_time <= 17:  # 15秒倒计时 + 2秒缓冲
            print("✅ 时序正常，拍照和语音确实是同时进行的")
        else:
            print("❌ 时序异常，可能存在阻塞问题")
        
        # 检查照片
        photo_path = os.path.join(current_dir, "current_image.jpg")
        if os.path.exists(photo_path):
            print("✅ 照片文件存在")
        else:
            print("❌ 照片文件不存在")
        
        context.logger.log_step("测试完成", f"总耗时: {total_time:.1f}秒, 拍照: {photo_success}")
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
        return 42
        
    except Exception as e:
        print(f"测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # 清理资源
        try:
            if 'context' in locals():
                context.cleanup()
        except:
            pass
    
    return 0

def test_camera_manager_speed():
    """测试CameraManager的速度"""
    print("=== 测试CameraManager拍照速度 ===")
    
    try:
        from core.camera.camera_manager import CameraManager
        
        # 测试1: 每次启动停止的拍照（旧方式）
        print("1. 测试每次启动停止的拍照...")
        start_time = time.time()
        camera1 = CameraManager()
        camera1.take_photo("test1.jpg")
        camera1.stop_camera()
        old_way_time = time.time() - start_time
        print(f"   耗时: {old_way_time:.2f} 秒")
        
        # 测试2: 预先启动的拍照（新方式）
        print("2. 测试预先启动的拍照...")
        camera2 = CameraManager()
        
        # 预先启动
        start_time = time.time()
        camera2.start_camera()
        startup_time = time.time() - start_time
        print(f"   启动时间: {startup_time:.2f} 秒")
        
        # 快速拍照
        start_time = time.time()
        camera2.take_photo("test2.jpg")
        quick_photo_time = time.time() - start_time
        print(f"   快速拍照时间: {quick_photo_time:.2f} 秒")
        
        camera2.stop_camera()
        
        print(f"\n速度对比:")
        print(f"- 旧方式总时间: {old_way_time:.2f} 秒")
        print(f"- 新方式启动时间: {startup_time:.2f} 秒")
        print(f"- 新方式拍照时间: {quick_photo_time:.2f} 秒")
        print(f"- 速度提升: {(old_way_time - quick_photo_time):.2f} 秒")
        
        if quick_photo_time < old_way_time:
            print("✅ 新方式确实更快")
        else:
            print("❌ 新方式没有提速")
        
        return True
        
    except Exception as e:
        print(f"CameraManager测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("修复后的拍照+语音功能测试")
    print("=" * 60)
    
    # 测试相机管理器速度
    print()
    if not test_camera_manager_speed():
        print("警告：相机测试失败，可能影响拍照+语音测试")
    
    # 测试拍照+语音时序
    print()
    exit_code = test_photo_voice_timing()
    
    print("=" * 60)
    sys.exit(exit_code) 