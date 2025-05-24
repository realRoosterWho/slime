#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试摄像头拍摄和OpenAI图像识别集成
验证：
1. 摄像头能成功拍摄照片
2. 照片能正确编码为base64
3. OpenAI能够识别和分析图像内容
4. 如果OpenAI无法识别，系统能正确处理
"""

import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.derive_context import DeriveContext
from core.components.derive_utils import run_camera_test, encode_image, DeriveChatUtils

def test_camera_openai_integration():
    """测试摄像头和OpenAI集成"""
    print("=== 测试摄像头和OpenAI图像识别集成 ===")
    
    context = None
    try:
        # 创建上下文
        context = DeriveContext("测试摄像头+OpenAI")
        
        # 步骤1：测试摄像头拍摄
        context.oled_display.show_text_oled(
            "步骤1: 摄像头测试\n"
            "准备拍照\n"
            "BT1拍照"
        )
        
        result = context.oled_display.wait_for_button_with_text(
            context.controller,
            "按BT1开始拍照测试",
            context=context
        )
        
        if result == 2:  # 长按返回
            return False
        
        # 开始拍照
        context.oled_display.show_text_oled("正在拍照...")
        print("📸 开始拍照...")
        
        run_camera_test()
        
        # 检查照片是否存在
        photo_path = os.path.join(context.get_project_root(), "current_image.jpg")
        
        if not os.path.exists(photo_path):
            context.oled_display.show_text_oled("❌ 拍照失败\n文件不存在")
            print("❌ 拍照失败：照片文件不存在")
            return False
        
        # 检查文件大小
        file_size = os.path.getsize(photo_path)
        if file_size == 0:
            context.oled_display.show_text_oled("❌ 拍照失败\n文件为空")
            print("❌ 拍照失败：照片文件为空")
            return False
        
        print(f"✅ 拍照成功：{photo_path}, 文件大小: {file_size} bytes")
        
        # 步骤2：显示照片（验证格式）
        try:
            from PIL import Image
            img = Image.open(photo_path)
            context.lcd_display.show_image(img)
            print(f"✅ 照片格式正确：{img.size}, 模式: {img.mode}")
        except Exception as e:
            context.oled_display.show_text_oled("❌ 照片格式错误")
            print(f"❌ 照片格式错误: {e}")
            return False
        
        # 步骤3：测试base64编码
        context.oled_display.show_text_oled(
            "步骤2: 编码测试\n"
            "Base64编码..."
        )
        time.sleep(1)
        
        try:
            base64_image = encode_image(photo_path)
            print(f"✅ Base64编码成功，长度: {len(base64_image)} 字符")
            
            if len(base64_image) < 100:
                raise ValueError("Base64编码异常短")
                
        except Exception as e:
            context.oled_display.show_text_oled("❌ 编码失败")
            print(f"❌ Base64编码失败: {e}")
            return False
        
        # 步骤4：测试OpenAI图像识别
        context.oled_display.show_text_oled(
            "步骤3: AI分析\n"
            "发送到OpenAI..."
        )
        print("🤖 开始OpenAI图像分析...")
        
        try:
            # 创建data URL
            data_url = f"data:image/jpeg;base64,{base64_image}"
            
            # 创建聊天工具
            chat_utils = DeriveChatUtils()
            
            # 构建测试提示
            test_prompt = "请简单描述这张照片中你看到的内容。如果你能看到图片，请以'我看到'开头回答。"
            
            input_content = [
                {"type": "input_text", "text": test_prompt},
                {"type": "input_image", "image_url": data_url}
            ]
            
            # 发送请求
            response = chat_utils.chat_with_continuity(input_content)
            
            print(f"🤖 OpenAI回复: {response}")
            
            # 分析回复内容
            success_indicators = ["我看到", "照片中", "图片中", "画面中", "可以看到"]
            failure_indicators = ["抱歉", "无法", "不能", "看不到", "无法查看"]
            
            is_success = any(indicator in response for indicator in success_indicators)
            is_failure = any(indicator in response for indicator in failure_indicators)
            
            if is_success and not is_failure:
                context.oled_display.show_text_oled(
                    "✅ AI识别成功\n"
                    f"{response[:30]}..."
                )
                print("✅ OpenAI图像识别成功！")
                result_success = True
            elif is_failure:
                context.oled_display.show_text_oled(
                    "⚠️ AI无法识别\n"
                    "检测到常见错误"
                )
                print("⚠️ OpenAI无法识别图像，检测到拒绝性回复")
                result_success = False
            else:
                context.oled_display.show_text_oled(
                    "❓ AI回复不明确\n"
                    "需要人工判断"
                )
                print("❓ OpenAI回复不明确，需要人工判断")
                result_success = None
            
            time.sleep(3)
            
            # 显示详细结果
            context.oled_display.show_text_oled(
                f"测试完成！\n"
                f"拍照: ✅\n"
                f"编码: ✅\n"
                f"AI识别: {'✅' if result_success else '⚠️' if result_success is False else '❓'}"
            )
            
            return result_success
            
        except Exception as e:
            context.oled_display.show_text_oled(
                "❌ AI分析异常\n"
                f"{str(e)[:20]}..."
            )
            print(f"❌ OpenAI分析异常: {e}")
            return False
        
    except Exception as e:
        print(f"测试异常: {e}")
        if context:
            context.oled_display.show_text_oled(f"测试异常:\n{str(e)[:20]}...")
        return False
    
    finally:
        if context:
            try:
                time.sleep(2)
                context.cleanup()
            except:
                pass

def main():
    """主函数"""
    print("开始摄像头和OpenAI集成测试...")
    
    result = test_camera_openai_integration()
    
    print(f"\n{'='*50}")
    print("测试结果:")
    if result is True:
        print("✅ 摄像头拍摄和OpenAI图像识别都正常工作")
    elif result is False:
        print("⚠️ OpenAI无法识别图像内容（已知问题）")
    elif result is None:
        print("❓ 测试结果不明确，需要进一步检查")
    else:
        print("❌ 测试失败，存在技术问题")
    
    return result

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success is not False else 1)
    except KeyboardInterrupt:
        print("\n用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"程序异常: {e}")
        sys.exit(1) 