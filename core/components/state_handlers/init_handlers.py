import time

class InitHandlers:
    """初始化相关的状态处理器"""
    
    def handle_init(self, state_machine):
        """处理初始化状态"""
        state_machine.logger.log_step("初始化", "根据文本开始新的漂流...")
        
        # 使用通用函数生成性格
        state_machine.data['personality'] = state_machine.generate_text('personality', text=state_machine.initial_text)
        state_machine.logger.log_step("性格生成", state_machine.data['personality'])
        
        # 提取史莱姆属性
        state_machine.extract_slime_attributes(state_machine.data['personality'])
        
        # 根据性格生成视觉描述
        state_machine.data['slime_description'] = state_machine.generate_text('slime_description', text=state_machine.data['personality'])
        state_machine.logger.log_step("外观描述", state_machine.data['slime_description'])
        
        # 保存详细的外观描述用于保持一致性
        state_machine.data['slime_appearance'] = f"一个可爱的史莱姆生物。{state_machine.data['slime_description']} 。"
        state_machine.logger.log_step("一致性外观描述", state_machine.data['slime_appearance'])
        
        state_machine.oled_display.show_text_oled("性格设定完成")
        time.sleep(1)

    def handle_gen_slime_image(self, state_machine):
        """处理生成史莱姆图片状态"""
        state_machine.oled_display.show_text_oled("正在生成\n史莱姆形象...")
        
        # 生成史莱姆的图片
        slime_prompt = state_machine.generate_image_prompt('slime')
        state_machine.logger.log_prompt("slime_image_prompt", slime_prompt)
        
        # 使用统一的图片生成方法
        state_machine.generate_image_with_retry(slime_prompt, 'slime_image', 'slime')

    def handle_show_slime_image(self, state_machine):
        """处理显示史莱姆图片状态"""
        state_machine.display_image_with_text(
            'slime_image',
            "史莱姆\n绘制完成！",
            "按BT1继续",
            "史莱姆图片显示成功",
            "跳过图片显示：图片未生成"
        )

    def handle_show_greeting(self, state_machine):
        """处理显示打招呼状态"""
        # 使用通用函数生成打招呼语句
        state_machine.data['greeting'] = state_machine.generate_text('greeting', text=state_machine.data['personality'])
        
        state_machine.logger.log_step("打招呼", state_machine.data['greeting'])
        state_machine.wait_for_button(f"史莱姆说：\n{state_machine.data['greeting']}")

    def handle_ask_photo(self, state_machine):
        """处理询问拍照状态"""
        # 使用通用函数生成询问语句
        photo_question = state_machine.generate_text('photo_question', text=state_machine.data['personality'])
        
        state_machine.logger.log_step("询问拍照", photo_question)
        state_machine.wait_for_button(f"史莱姆说：\n{photo_question}") 