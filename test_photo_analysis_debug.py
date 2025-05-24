#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试照片分析问题专用测试
重点验证：
1. 拍照功能
2. 文件路径处理
3. Base64编码
4. OpenAI API请求格式
5. 响应内容分析
"""

import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.derive_context import DeriveContext
from core.components.states.take_photo_with_voice_state import TakePhotoWithVoiceState
from core.components.states.process_photo_voice_state import ProcessPhotoVoiceState

def test_photo_analysis_debug():
    """调试照片分析流程"""
    print("=== 调试照片分析问题 ===")
    
    context = None
    try:
        # 创建上下文
        context = DeriveContext("调试照片分析")
        
        # 显示测试信息
        context.oled_display.show_text_oled(
            "调试照片分析\n"
            "将会进行详细\n"
            "调试信息输出"
        )
        time.sleep(2)
        
        print("🔍 开始调试流程...")
        
        # 步骤1：拍照+语音
        print("\n📸 步骤1：拍照+语音录制")
        take_photo_state = TakePhotoWithVoiceState()
        take_photo_state.execute(context)
        
        # 检查拍照结果
        photo_path = context.get_data('timestamped_image')
        voice_text = context.get_data('photo_voice_text')
        
        print(f"📸 拍照结果: {photo_path}")
        print(f"🗣️ 语音结果: {voice_text[:50] if voice_text else 'None'}...")
        
        if not photo_path:
            print("❌ 拍照失败，无法继续测试")
            return False
        
        # 步骤2：分析照片+语音  
        print("\n🤖 步骤2：分析照片+语音")
        process_state = ProcessPhotoVoiceState()
        process_state.execute(context)
        
        # 检查分析结果
        analysis_result = context.get_data('photo_description')
        
        print(f"🤖 分析结果: {analysis_result[:100] if analysis_result else 'None'}...")
        
        # 显示完成信息
        context.oled_display.show_text_oled(
            "调试完成\n"
            "查看控制台\n"
            "详细日志"
        )
        
        # 等待用户查看日志
        result = context.oled_display.wait_for_button_with_text(
            context.controller,
            "调试完成\n详细日志已输出\n\n按BT1结束",
            context=context
        )
        
        return True
        
    except Exception as e:
        print(f"调试过程异常: {e}")
        if context:
            context.oled_display.show_text_oled(f"调试异常:\n{str(e)[:20]}...")
        return False
    
    finally:
        if context:
            try:
                time.sleep(1)
                context.cleanup()
            except:
                pass

def main():
    """主函数"""
    print("开始照片分析调试...")
    
    result = test_photo_analysis_debug()
    
    print(f"\n{'='*50}")
    print("调试结果:")
    if result:
        print("✅ 调试流程完成，请查看上面的详细日志")
        print("🔍 重点关注:")
        print("   - 📁 文件路径是否正确")
        print("   - 📏 文件大小是否正常")
        print("   - 🖼️ 图片格式是否有效")
        print("   - 🔤 Base64编码是否成功")
        print("   - 📨 AI回复内容是否包含拒绝性关键词")
    else:
        print("❌ 调试流程失败")
    
    return result

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断调试")
        sys.exit(1)
    except Exception as e:
        print(f"程序异常: {e}")
        sys.exit(1) 