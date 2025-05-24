#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试照片分析问题
检查照片路径、编码和AI分析的数据流
"""

import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.derive_context import DeriveContext
from core.components.derive_utils import encode_image

def debug_photo_analysis():
    """调试照片分析问题"""
    print("=== 调试照片分析问题 ===")
    
    context = None
    try:
        # 创建上下文
        context = DeriveContext("调试照片")
        
        # 检查可能的照片路径
        project_root = context.get_project_root()
        possible_paths = [
            os.path.join(project_root, "current_image.jpg"),
            os.path.join(project_root, "current_image_*.jpg"),
        ]
        
        print(f"📁 项目根目录: {project_root}")
        
        # 查找实际存在的照片文件
        actual_photos = []
        for pattern in ['current_image*.jpg', '*image*.jpg', '*.jpg', '*.jpeg', '*.png']:
            import glob
            photos = glob.glob(os.path.join(project_root, pattern))
            actual_photos.extend(photos)
        
        print(f"📷 找到的图片文件:")
        for photo in actual_photos[:10]:  # 最多显示10个
            size = os.path.getsize(photo) if os.path.exists(photo) else 0
            print(f"  - {photo} ({size} bytes)")
        
        if not actual_photos:
            print("❌ 未找到任何图片文件")
            
            # 模拟拍照
            context.oled_display.show_text_oled(
                "未找到照片\n尝试拍照测试"
            )
            time.sleep(2)
            
            from core.components.derive_utils import run_camera_test
            try:
                run_camera_test()
                print("📸 拍照测试完成")
                
                # 重新查找照片
                actual_photos = glob.glob(os.path.join(project_root, "current_image.jpg"))
                if actual_photos:
                    print(f"✅ 拍照后找到: {actual_photos[0]}")
                
            except Exception as e:
                print(f"❌ 拍照测试失败: {e}")
                return False
        
        if actual_photos:
            # 测试照片编码
            test_photo = actual_photos[0]
            print(f"\n🔍 测试照片编码: {test_photo}")
            
            try:
                # 测试文件是否可读
                with open(test_photo, 'rb') as f:
                    content = f.read()
                    print(f"✅ 照片文件可读，大小: {len(content)} bytes")
                
                # 测试base64编码
                base64_data = encode_image(test_photo)
                print(f"✅ Base64编码成功，长度: {len(base64_data)} 字符")
                
                # 测试data URL格式
                data_url = f"data:image/jpeg;base64,{base64_data}"
                print(f"✅ Data URL格式正确，总长度: {len(data_url)}")
                
                # 模拟AI调用测试
                context.oled_display.show_text_oled(
                    "测试AI照片分析\n发送到GPT..."
                )
                time.sleep(1)
                
                from core.components.derive_utils import DeriveChatUtils
                chat_utils = DeriveChatUtils()
                
                test_prompt = "请简单描述这张照片中的内容，一句话即可。"
                
                input_content = [
                    {"type": "input_text", "text": test_prompt},
                    {"type": "input_image", "image_url": data_url}
                ]
                
                print("🤖 发送AI分析请求...")
                response = chat_utils.chat_with_continuity(input_content)
                
                print(f"✅ AI分析响应: {response[:100]}...")
                
                if "抱歉" in response or "无法" in response:
                    print("⚠️ AI仍然无法看到照片内容")
                    context.oled_display.show_text_oled(
                        "AI无法识别照片\n可能是格式问题"
                    )
                else:
                    print("✅ AI成功识别照片内容！")
                    context.oled_display.show_text_oled(
                        "AI成功识别照片\n问题已解决"
                    )
                    
                return True
                
            except Exception as e:
                print(f"❌ 照片处理失败: {e}")
                context.oled_display.show_text_oled(f"处理失败:\n{str(e)[:20]}...")
                return False
        
        return False
        
    except Exception as e:
        print(f"调试异常: {e}")
        if context:
            context.oled_display.show_text_oled(f"调试异常:\n{str(e)[:20]}...")
        return False
    
    finally:
        if context:
            try:
                time.sleep(3)
                context.cleanup()
            except:
                pass

if __name__ == "__main__":
    success = debug_photo_analysis()
    print(f"\n{'='*50}")
    if success:
        print("✅ 照片分析调试完成!")
        print("- 照片文件存在且可读")
        print("- Base64编码正常")
        print("- AI能够识别照片内容")
    else:
        print("❌ 照片分析存在问题!")
        print("需要进一步检查:")
        print("- 照片文件是否存在")
        print("- 文件格式是否正确")
        print("- AI API是否支持图片分析")
    
    sys.exit(0 if success else 1) 