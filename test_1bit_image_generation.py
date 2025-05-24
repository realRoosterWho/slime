#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试1-bit风格图像生成并显示
"""

import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.derive_context import DeriveContext
from core.components.states.gen_slime_image_state import GenSlimeImageState
from core.components.states.generate_reward_image_state import GenerateRewardImageState

def test_1bit_image_generation():
    """测试1-bit风格图像生成并显示"""
    print("=== 测试1-bit风格图像生成与显示 ===")
    
    try:
        # 创建上下文
        context = DeriveContext("测试1-bit图像生成")
        
        # 设置测试数据
        context.set_data('slime_description', '一个好奇的小史莱姆，有着圆圆的眼睛和可爱的笑容')
        context.set_slime_attribute('quirk', '喜欢收集各种闪亮的小宝石和水晶')
        context.set_slime_attribute('reflex', '看到新事物会好奇地围绕它转圈')
        context.set_slime_attribute('obsession', '寻找世界上最亮的宝石')
        context.set_data('reward_level', 'great')
        context.set_data('reward_description', '一个魔法宝石收集盒')
        
        print("\n🎮 开始测试1-bit黑白像素风格图像生成...")
        context.oled_display.show_text_oled("1-bit图像生成\n测试开始...")
        time.sleep(2)
        
        # 用户选择测试项目
        choice = get_user_choice(context)
        
        if choice == 1:
            test_slime_image(context)
        elif choice == 2:
            test_reward_image(context)
        elif choice == 3:
            test_both_images(context)
        else:
            print("❌ 无效选择，退出测试")
            return
        
        print("\n✅ 1-bit风格图像生成测试完成！")
        context.oled_display.show_text_oled("测试完成\n按BT1退出")
        context.oled_display.wait_for_button_with_text(
            context.controller,
            "1-bit图像测试完成\n\n按BT1退出",
            context=context
        )
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        context.oled_display.show_text_oled(f"测试出错:\n{str(e)[:20]}...")
        import traceback
        traceback.print_exc()
        time.sleep(3)
    finally:
        context.cleanup()

def get_user_choice(context):
    """获取用户选择"""
    context.oled_display.show_text_oled(
        "选择测试项目:\n"
        "BT1 - 史莱姆图像\n"
        "BT2 - 奖励图像\n"
        "摇杆下 - 全部测试"
    )
    
    print("\n请选择测试项目:")
    print("1. 按BT1 - 测试史莱姆图像生成")
    print("2. 按BT2 - 测试奖励图像生成") 
    print("3. 摇杆下 - 测试全部图像")
    
    # 等待用户输入
    while True:
        try:
            # 检查按钮1
            if context.controller.get_button_state('BTN1'):
                print("选择: 史莱姆图像")
                time.sleep(0.3)  # 防抖
                return 1
                
            # 检查按钮2
            if context.controller.get_button_state('BTN2'):
                print("选择: 奖励图像")
                time.sleep(0.3)  # 防抖
                return 2
                
            # 检查摇杆下
            inputs = context.controller.check_inputs()
            if inputs.get('JOY_DOWN', False):
                print("选择: 全部测试")
                time.sleep(0.3)  # 防抖
                return 3
                
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\n用户中断测试")
            return 0

def test_slime_image(context):
    """测试史莱姆图像生成"""
    print("\n1. 🧪 测试史莱姆图像生成（1-bit风格）...")
    
    try:
        slime_state = GenSlimeImageState()
        
        # 显示提示词预览
        prompt = slime_state._generate_slime_prompt(context)
        print(f"史莱姆1-bit提示词预览：\n{prompt[:150]}...")
        
        # 检查关键1-bit词汇
        key_terms = ['1-bit', 'BLACK AND WHITE', 'monochrome', 'Game Boy']
        found_terms = [term for term in key_terms if term in prompt]
        print(f"✅ 找到1-bit关键词: {found_terms}")
        
        # 实际执行图像生成
        context.oled_display.show_text_oled("正在生成\n1-bit史莱姆...")
        slime_state.execute(context)
        
        # 检查是否生成成功
        slime_image_path = context.get_data('slime_image')
        if slime_image_path:
            print(f"✅ 史莱姆图像生成成功: {slime_image_path}")
            
            # 在LCD上显示图像
            from PIL import Image
            img = Image.open(slime_image_path)
            context.lcd_display.show_image(img)
            print("🖼️ 史莱姆图像已在LCD上显示")
            
            # 等待用户查看
            context.oled_display.wait_for_button_with_text(
                context.controller,
                "1-bit史莱姆图像\n已在LCD显示\n\n按BT1继续",
                context=context
            )
        else:
            print("❌ 史莱姆图像生成失败")
            
    except Exception as e:
        print(f"❌ 史莱姆图像测试失败: {e}")

def test_reward_image(context):
    """测试奖励图像生成"""
    print("\n2. 🎁 测试奖励图像生成（1-bit风格）...")
    
    try:
        reward_state = GenerateRewardImageState()
        
        # 实际执行图像生成
        context.oled_display.show_text_oled("正在生成\n1-bit奖励...")
        reward_state.execute(context)
        
        # 检查是否生成成功
        reward_image_path = context.get_data('reward_image_path')
        if reward_image_path:
            print(f"✅ 奖励图像生成成功: {reward_image_path}")
            
            # 在LCD上显示图像
            from PIL import Image
            img = Image.open(reward_image_path)
            context.lcd_display.show_image(img)
            print("🖼️ 奖励图像已在LCD上显示")
            
            # 等待用户查看
            context.oled_display.wait_for_button_with_text(
                context.controller,
                "1-bit奖励图像\n已在LCD显示\n\n按BT1继续",
                context=context
            )
        else:
            print("❌ 奖励图像生成失败")
            
    except Exception as e:
        print(f"❌ 奖励图像测试失败: {e}")

def test_both_images(context):
    """测试两种图像生成"""
    print("\n3. 🎮 测试全部1-bit图像生成...")
    
    # 先测试史莱姆
    test_slime_image(context)
    
    # 再测试奖励
    context.set_data('reward_level', 'encouragement')  # 也测试encouragement级
    context.set_data('reward_description', '一个神秘的史莱姆蛋')
    test_reward_image(context)
    
    print("🎉 全部1-bit图像测试完成！")

if __name__ == "__main__":
    test_1bit_image_generation() 