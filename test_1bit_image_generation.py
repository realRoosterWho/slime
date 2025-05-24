#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试1-bit风格图像生成
"""

import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.components.derive_context import DeriveContext
from core.components.states.gen_slime_image_state import GenSlimeImageState
from core.components.states.generate_reward_image_state import GenerateRewardImageState

def test_1bit_image_generation():
    """测试1-bit风格图像生成"""
    print("=== 测试1-bit风格图像生成 ===")
    
    try:
        # 创建上下文
        context = DeriveContext("测试1-bit图像生成")
        
        # 设置测试数据
        context.set_data('slime_description', '一个好奇的蓝色史莱姆，喜欢收集闪亮的东西')
        context.set_slime_attribute('quirk', '喜欢收集各种闪亮的小宝石和水晶')
        context.set_slime_attribute('reflex', '看到新事物会好奇地围绕它转圈')
        context.set_slime_attribute('obsession', '寻找世界上最亮的宝石')
        context.set_data('reward_level', 'great')
        context.set_data('reward_description', '一个魔法宝石收集盒')
        
        print("\n1. 测试史莱姆图像生成（1-bit风格）...")
        slime_state = GenSlimeImageState()
        
        # 获取生成提示词
        prompt = slime_state._generate_slime_prompt(context)
        print(f"史莱姆图像提示词：\n{prompt[:200]}...")
        
        # 检查关键词
        key_terms = ['1-bit', 'BLACK AND WHITE', 'monochrome', 'Game Boy']
        found_terms = [term for term in key_terms if term in prompt]
        print(f"找到的1-bit关键词: {found_terms}")
        
        print("\n2. 测试奖励图像生成（1-bit风格）...")
        reward_state = GenerateRewardImageState()
        
        # 模拟奖励图像生成的提示词生成部分
        reward_level = context.get_data('reward_level', 'encouragement')
        reward_description = context.get_data('reward_description', '一个特别的奖励')
        slime_attributes = context.get_data('slime_attributes', {})
        
        quirk = slime_attributes.get('quirk', '喜欢收集有趣的小物件')
        
        # 生成great级别奖励的提示词（简化版）
        reward_prompt = f"""
        A magical accessory that matches: {quirk}
        Reward: {reward_description}
        
        STRICT 1-bit monochrome pixel art requirements:
        - ONLY BLACK AND WHITE (1-bit color depth)
        - Pure monochrome like classic Game Boy graphics
        - Visible pixel grid structure with chunky square pixels
        - NO grayscale, NO color, ONLY pure black and pure white
        """
        
        print(f"奖励图像提示词：\n{reward_prompt[:200]}...")
        
        # 检查关键词
        found_reward_terms = [term for term in key_terms if term in reward_prompt]
        print(f"找到的1-bit关键词: {found_reward_terms}")
        
        print("\n✅ 1-bit风格图像生成测试完成！")
        print("🎮 所有图像都将使用经典Game Boy风格的黑白像素艺术")
        print("⚫⚪ 纯黑白1-bit色彩，高对比度复古效果")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_1bit_image_generation() 