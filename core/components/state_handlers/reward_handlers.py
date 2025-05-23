import os
import time

class RewardHandlers:
    """奖励相关的状态处理器"""
    
    def handle_analyze_reward(self, state_machine):
        """处理分析奖励状态"""
        state_machine.oled_display.show_text_oled("正在分析\n奖励...")
        
        # 调用奖励分析
        reward_response = state_machine.generate_text(
            'analyze_reward',
            personality=state_machine.data['personality'],
            obsession=state_machine.data['slime_attributes']['obsession'],
            quirk=state_machine.data['slime_attributes']['quirk'],
            reflex=state_machine.data['slime_attributes']['reflex'],
            photo_description=state_machine.data['new_photo_description']
        )
        
        # 解析响应
        default_values = {
            "is_matched": False,
            "reward_type": "egg",
            "reward_description": "一个彩色的史莱姆蛋，有着闪烁的表面和不规则的花纹",
            "reward_text": "意外收获的史莱姆蛋"
        }
        
        state_machine.logger.log_step("奖励JSON响应", reward_response)
        reward_data = state_machine.parse_json_response(reward_response, default_values)
        
        # 保存奖励数据
        state_machine.data['is_obsession_matched'] = reward_data.get('is_matched', False)
        state_machine.data['reward_type'] = reward_data.get('reward_type', 'egg')
        state_machine.data['reward_description'] = reward_data.get('reward_description', '')
        state_machine.data['reward_text'] = reward_data.get('reward_text', '')
        
        # 记录本次奖励
        reward_info = {
            'cycle': state_machine.data['cycle_count'],
            'type': state_machine.data['reward_type'],
            'text': state_machine.data['reward_text'],
            'is_matched': state_machine.data['is_obsession_matched']
        }
        state_machine.data['all_rewards'].append(reward_info)
        
        state_machine.logger.log_step("奖励分析", f"是否匹配执念: {state_machine.data['is_obsession_matched']}, 奖励类型: {state_machine.data['reward_type']}")
        state_machine.logger.log_step("奖励描述", state_machine.data['reward_description'])
        state_machine.logger.log_step("奖励文本", state_machine.data['reward_text'])

    def handle_generate_reward_image(self, state_machine):
        """处理生成奖励图片状态"""
        # 根据奖励类型生成不同的提示词
        if state_machine.data['reward_type'] == 'accessory':
            prompt = f"""一个奇幻的史莱姆装饰品。{state_machine.data['reward_description']} 
            精致细腻，色彩鲜艳，儿童绘本风格，白色背景，特写镜头。这个装饰品适合用在史莱姆身上：{state_machine.data['slime_appearance']}"""
        else:  # egg类型
            prompt = f"""一个神秘的史莱姆蛋。{state_machine.data['reward_description']} 
            表面有闪光和微妙的纹理，儿童绘本风格，白色背景，特写镜头。"""
        
        state_machine.logger.log_prompt("reward_image_prompt", prompt)
        
        # 使用统一的图片生成方法
        reward_image = state_machine.generate_image_with_retry(prompt, 'reward_image', 'reward')
        
        # 记录奖励到总列表
        reward_record = {
            'type': state_machine.data['reward_type'],
            'description': state_machine.data['reward_description'],
            'text': state_machine.data['reward_text'],
            'image': reward_image
        }
        state_machine.data['all_rewards'].append(reward_record)
        
        # 保存奖励列表到日志
        state_machine.logger.log_step("奖励记录", f"当前获得的奖励数量: {len(state_machine.data['all_rewards'])}")

    def handle_show_reward(self, state_machine):
        """处理显示奖励状态"""
        state_machine.display_image_with_text(
            'reward_image',
            f"奖励:\n{state_machine.data['reward_text']}",
            "按BT1继续",
            "奖励图片显示成功",
            "跳过奖励图片显示：图片未生成"
        ) 