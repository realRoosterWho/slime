import os
import shutil
from PIL import Image
from ..derive_utils import run_camera_test, encode_image

class PhotoHandlers:
    """拍照相关的状态处理器"""
    
    def handle_take_photo(self, state_machine):
        """处理拍照状态"""
        return self._take_photo_common(state_machine, is_new_photo=False)

    def handle_take_new_photo(self, state_machine):
        """处理拍摄新照片状态"""
        return self._take_photo_common(state_machine, is_new_photo=True)

    def _take_photo_common(self, state_machine, is_new_photo=False):
        """统一的拍照处理方法
        Args:
            is_new_photo (bool): True表示是新照片，False表示是第一张照片
        """
        # 根据是否为新照片显示不同的提示文本
        if is_new_photo:
            display_text = "准备拍摄新照片\n请按下BT1按钮"
            button_text = "按下BT1按钮拍照"
            log_step = "新照片"
        else:
            display_text = "准备拍照\n请按下BT1按钮"
            button_text = "按下BT1按钮拍照"
            log_step = "拍照"
        
        state_machine.oled_display.show_text_oled(display_text)
        
        # 等待用户按下按钮1拍照
        state_machine.wait_for_button(button_text)
        
        state_machine.oled_display.show_text_oled("正在拍照...")
        
        # 运行相机脚本拍照
        run_camera_test()
        
        # 查找最新拍摄的照片
        try:
            # 先检查项目根目录是否有照片
            photo_path = os.path.join(state_machine.get_project_root(), "current_image.jpg")
            if not os.path.exists(photo_path):
                raise FileNotFoundError("未找到拍摄的照片")
            
            # 保存带时间戳的照片副本
            timestamped_key = state_machine.save_photo_with_timestamp(photo_path, is_new_photo)
            
            # 在LCD上显示照片
            img = Image.open(photo_path)
            state_machine.lcd_display.show_image(img)
            
            state_machine.logger.log_step(log_step, f"{'新' if is_new_photo else ''}照片已保存: {state_machine.data[timestamped_key]}")
            
            # 等待用户确认照片
            state_machine.oled_display.show_text_oled("照片已拍摄\n按BT1继续")
            state_machine.wait_for_button("按BT1继续")
            
        except Exception as e:
            error_msg = f"处理{'新' if is_new_photo else ''}照片时出错: {str(e)}"
            state_machine.handle_error(error_msg, "照片处理失败\n请重试")
            # 出错时递归重试
            return self._take_photo_common(state_machine, is_new_photo)

    def handle_analyze_photo(self, state_machine):
        """处理分析照片状态"""
        state_machine.oled_display.show_text_oled("正在分析\n照片...")
        
        base64_image = encode_image(state_machine.data['timestamped_image'])
        data_url = f"data:image/jpeg;base64,{base64_image}"
        
        # 完全使用与 openai_test.py 相同的格式
        input_content = [
            {"type": "input_text", "text": "请详细描述这张照片的内容以及给人带来的感受。"},
            {"type": "input_image", "image_url": data_url}
        ]
        
        state_machine.data['photo_description'] = state_machine.chat_with_continuity(input_content)
        
        state_machine.logger.log_step("照片分析", state_machine.data['photo_description'])
        
    def handle_suggest_destination(self, state_machine):
        """处理建议目的地状态 - 优化用户体验"""
        state_machine.oled_display.show_text_oled("正在思考\n建议...")
        
        try:
            # 尝试生成更具体的建议
            suggestion_prompt = f"""
            基于照片内容和史莱姆的执念，生成一个具体的建议，引导玩家寻找符合执念的场景。
            
            照片内容: {state_machine.data['photo_description']}
            史莱姆执念: {state_machine.data['slime_attributes']['obsession']}
            互动语气: {state_machine.data['slime_attributes']['tone']}
            
            请提供:
            1. 一个简短的建议(不超过20个字)
            2. 一个简短的理由，为什么这个方向与执念相关
            
            回复格式:
            {{"suggestion": "建议", "reason": "理由"}}
            """
            
            response = state_machine.chat_with_continuity(
                system_content="你是一个善于引导探索的史莱姆，你会根据照片内容和自己的执念，给出有针对性的建议。",
                prompt=suggestion_prompt
            )
            
            suggestion_data = state_machine.parse_json_response(response, {"suggestion": "去寻找更多有趣的东西吧！", "reason": "可能会符合我的执念"})
            suggestion = suggestion_data.get("suggestion", "去寻找更多有趣的东西吧！")
            reason = suggestion_data.get("reason", "")
            
            # 记录建议
            state_machine.data['destination_suggestion'] = suggestion
            state_machine.logger.log_step("建议目的地", f"建议: {suggestion}, 理由: {reason}")
            
            # 显示建议和理由
            display_text = f"史莱姆说：\n{suggestion}"
            if reason and len(reason) < 30:  # 如果理由不太长，也一并显示
                display_text += f"\n\n{reason}"
            
            state_machine.wait_for_button(display_text)
            
        except Exception as e:
            # 使用统一错误处理
            state_machine.handle_error(f"生成建议时出错: {str(e)}")
            
            # 使用备用建议
            default_suggestion = "去寻找更多有趣的东西吧！"
            state_machine.data['destination_suggestion'] = default_suggestion
            state_machine.logger.log_step("建议目的地", f"使用默认建议: {default_suggestion}")
            state_machine.wait_for_button(f"史莱姆说：\n{default_suggestion}")

    def handle_wait_for_new_photo(self, state_machine):
        """处理等待新照片状态"""
        # 生成一个有关执念的等待提示
        waiting_prompt = state_machine.generate_text(
            'waiting_prompt', 
            obsession=state_machine.data['slime_attributes']['obsession'],
            tone=state_machine.data['slime_attributes']['tone']  # 添加缺少的tone参数
        )
        
        state_machine.logger.log_step("等待新照片", waiting_prompt)
        state_machine.wait_for_button(f"史莱姆说：\n{waiting_prompt}\n\n按下按钮1继续拍照")

    def handle_analyze_new_photo(self, state_machine):
        """处理分析新照片状态"""
        state_machine.oled_display.show_text_oled("正在分析\n照片...")
        
        base64_image = encode_image(state_machine.data['new_timestamped_image'])
        data_url = f"data:image/jpeg;base64,{base64_image}"
        
        # 使用与前面相同的格式来分析图片
        input_content = [
            {"type": "input_text", "text": "请详细描述这张照片的内容以及给人带来的感受，尤其是与'" + 
             state_machine.data['slime_attributes']['obsession'] + "'相关的内容。"},
            {"type": "input_image", "image_url": data_url}
        ]
        
        state_machine.data['new_photo_description'] = state_machine.chat_with_continuity(input_content)
        
        state_machine.logger.log_step("新照片分析", state_machine.data['new_photo_description'])
        state_machine.oled_display.show_text_oled("分析完成！") 