import os
import time
import RPi.GPIO as GPIO

class FeedbackHandlers:
    """反馈和总结相关的状态处理器"""
    
    def handle_generate_feedback(self, state_machine):
        """处理生成反馈状态"""
        state_machine.oled_display.show_text_oled("正在生成\n反馈...")
        
        # 创建反馈提示词
        if state_machine.data['is_obsession_matched']:
            feedback_prompt = f"""
            史莱姆的执念得到了满足！请根据以下信息生成史莱姆的正面反馈：
            
            史莱姆的性格: {state_machine.data['personality']}
            互动语气: {state_machine.data['slime_attributes']['tone']}
            照片内容: {state_machine.data['new_photo_description']}
            奖励物品: {state_machine.data['reward_text']}
            
            请提供两部分内容：
            1. 反馈文本: 简短的反馈语(不超过20个字)，史莱姆应该很开心
            2. 反馈描述: 描述史莱姆开心的表情和动作(用于生成图片)
            
            请以JSON格式返回：
            {{"feedback_text": "反馈文本", "feedback_description": "反馈描述"}}
            """
        else:
            feedback_prompt = f"""
            史莱姆的执念没有得到满足，但发现了意外惊喜。请根据以下信息生成史莱姆的反馈：
            
            史莱姆的性格: {state_machine.data['personality']}
            偏执反应: {state_machine.data['slime_attributes']['reflex']}
            互动语气: {state_machine.data['slime_attributes']['tone']}
            照片内容: {state_machine.data['new_photo_description']}
            奖励物品: {state_machine.data['reward_text']}
            
            请提供两部分内容：
            1. 反馈文本: 简短的反馈语(不超过20个字)，史莱姆应该有些意外但不失望
            2. 反馈描述: 描述史莱姆好奇或惊讶的表情和动作(用于生成图片)
            
            请以JSON格式返回：
            {{"feedback_text": "反馈文本", "feedback_description": "反馈描述"}}
            """
        
        # 生成反馈
        feedback_response = state_machine.chat_with_continuity(
            system_content="你是一个创意角色反馈生成器。请根据角色性格生成真实、具体的反馈内容。",
            prompt=feedback_prompt
        )
        
        state_machine.logger.log_response("feedback_response", feedback_response)
        state_machine.logger.log_step("反馈JSON响应", feedback_response)
        
        # 解析反馈响应
        default_feedback = {
            "feedback_text": "谢谢你的努力！" if state_machine.data['is_obsession_matched'] else "这个也不错呢~",
            "feedback_description": "史莱姆开心地跳跃，眼睛闪烁着喜悦的光芒" if state_machine.data['is_obsession_matched'] 
                                  else "史莱姆歪着头，眼睛里充满好奇和一丝惊喜"
        }
        
        feedback_data = state_machine.parse_json_response(feedback_response, default_feedback)
        
        # 保存反馈数据
        state_machine.data['feedback_text'] = feedback_data.get('feedback_text', default_feedback['feedback_text'])
        state_machine.data['feedback_description'] = feedback_data.get('feedback_description', default_feedback['feedback_description'])
        
        state_machine.logger.log_step("反馈文本", state_machine.data['feedback_text'])
        state_machine.logger.log_step("反馈描述", state_machine.data['feedback_description'])
        
        # 生成反馈图片
        feedback_prompt = f"""一个生动的史莱姆表情反应。{state_machine.data['slime_appearance']} 
        表情生动，{state_machine.data['feedback_description']} 儿童绘本风格，明亮的背景，色彩鲜艳。"""
        
        state_machine.logger.log_prompt("feedback_image_prompt", feedback_prompt)
        
        # 使用统一的图片生成方法
        state_machine.generate_image_with_retry(feedback_prompt, 'feedback_image', 'feedback')

    def handle_show_feedback(self, state_machine):
        """处理显示反馈状态"""
        # 如果图片存在，使用统一显示方法；否则只显示文本
        if state_machine.data.get('feedback_image') and os.path.exists(state_machine.data['feedback_image']):
            state_machine.display_image_with_text(
                'feedback_image',
                f"史莱姆说：\n{state_machine.data['feedback_text']}",
                "按BT1继续",
                "反馈图片显示成功"
            )
        else:
            state_machine.logger.log_step("显示反馈", "跳过反馈图片显示：图片未生成")
            state_machine.wait_for_button(f"史莱姆说：\n{state_machine.data['feedback_text']}\n\n按BT1继续")

    def handle_ask_continue(self, state_machine):
        """处理询问是否继续状态"""
        # 生成继续询问文本
        continue_question = state_machine.generate_text(
            'continue_question',
            personality=state_machine.data['personality'],
            tone=state_machine.data['slime_attributes']['tone']  # 添加tone参数
        )
        
        state_machine.logger.log_step("询问继续", f"询问文本: {continue_question}")
        
        # 使用新的 show_continue_drift_option 方法显示选择界面
        state_machine.data['continue_derive'] = state_machine.oled_display.show_continue_drift_option(
            state_machine.controller,
            question=continue_question
        )
        
        # 记录用户选择
        if state_machine.data['continue_derive']:
            state_machine.logger.log_step("用户选择", "继续漂流")
            state_machine.oled_display.show_text_oled("准备继续漂流...")
        else:
            state_machine.logger.log_step("用户选择", "结束漂流")
            state_machine.oled_display.show_text_oled("准备结束漂流...")
        
        time.sleep(1)

    def handle_summary(self, state_machine):
        """处理总结状态 - 增强版"""
        state_machine.oled_display.show_text_oled("正在总结\n漂流经历...")
        
        try:
            # 构建漂流总结的提示词
            cycle_count = state_machine.data['cycle_count']
            rewards_list = []
            
            for i, reward in enumerate(state_machine.data['all_rewards']):
                match_status = "符合执念" if reward.get('is_matched', False) else "不符合执念"
                rewards_list.append(f"{reward.get('text', '奖励')} ({match_status})")
            
            rewards_text = "、".join(rewards_list) if rewards_list else "没有获得奖励"
            
            summary_prompt = f"""
            请以史莱姆的口吻，总结这次漂流经历。满足以下要求：
            
            1. 使用史莱姆的互动语气：{state_machine.data['slime_attributes']['tone']}
            2. 提到玩家完成了{cycle_count+1}次漂流
            3. 提到获得的奖励：{rewards_text}
            4. 表达对这次漂流的感受
            5. 说一句温馨的告别
            
            总结控制在50字以内，情感要真挚，展现史莱姆的性格特点。
            """
            
            # 生成总结
            state_machine.data['summary'] = state_machine.chat_with_continuity(
                system_content="你是一个充满个性的史莱姆，正在与玩家告别。你的回复应当情感丰富，符合你的性格特点。",
                prompt=summary_prompt
            )
            
            state_machine.logger.log_step("漂流总结", state_machine.data['summary'])
            
            # 生成总结图片
            summary_image_prompt = f"""
            一个可爱的史莱姆正在告别。{state_machine.data['slime_appearance']}
            史莱姆表情带有一丝不舍但很满足，背景有漂流中收集到的物品和记忆。
            如果有获得装饰物奖励，史莱姆应该佩戴着这些装饰。
            画面温馨感人，色彩明亮但带有一丝离别的感伤。
            儿童绘本风格，高质量插画，细节丰富。
            """
            
            # 尝试生成总结图片，不强制要求成功
            try:
                state_machine.generate_image_with_retry(summary_image_prompt, 'summary_image', 'summary')
            except Exception:
                # 图片生成失败不影响总结流程
                state_machine.logger.log_step("总结图片", "总结图片生成失败，将只显示文字")
            
            # 显示总结（优先显示图片，否则只显示文字）
            if state_machine.data.get('summary_image') and os.path.exists(state_machine.data['summary_image']):
                state_machine.display_image_with_text(
                    'summary_image',
                    f"史莱姆说：\n{state_machine.data['summary']}",
                    "按BT1结束漂流",
                    "总结图片显示成功"
                )
            else:
                state_machine.wait_for_button(f"史莱姆说：\n{state_machine.data['summary']}\n\n按BT1结束漂流")
                
            # 再见图像
            final_text = "感谢体验\n史莱姆漂流!"
            state_machine.oled_display.show_text_oled(final_text)
            time.sleep(3)
        
        except Exception as e:
            # 使用统一的错误处理
            state_machine.handle_error(f"生成总结时出错: {str(e)}")
            
            # 使用默认总结
            state_machine.data['summary'] = "谢谢你陪我漂流！希望我们的旅程给你带来了快乐，下次再见！"
            state_machine.logger.log_step("漂流总结", f"使用默认总结: {state_machine.data['summary']}")
            state_machine.wait_for_button(f"史莱姆说：\n{state_machine.data['summary']}\n\n按BT1结束漂流")

    def handle_cleanup(self, state_machine):
        """处理清理状态"""
        try:
            # 先保存日志
            if not state_machine.state.name == 'EXIT':  # 如果不是正常退出，记录一下
                state_machine.logger.log_step("清理", "程序结束，清理资源")
                state_machine.logger.save_log()
            
            # 清理 GPIO
            GPIO.cleanup()
            
            # 清理其他资源
            state_machine.controller.cleanup()
            state_machine.lcd_display.clear()
            state_machine.oled_display.clear()
            
        except Exception as e:
            print(f"清理过程中出错: {e}")
        return 