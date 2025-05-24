import subprocess
import os
import sys
import base64
import requests
import time
import json
import shutil
from openai import OpenAI
from dotenv import load_dotenv
import RPi.GPIO as GPIO
from PIL import Image
from io import BytesIO
import replicate

# 导入性能优化器
from .performance_optimizer import global_optimizer, cached_api_call

# 加载环境变量
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=90.0  # 增加超时时间到90秒，避免长时间API调用超时
)

def chat_with_gpt(input_content, system_content=None, previous_response_id=None):
    """与GPT进行对话"""
    input_data = [{"role": "user", "content": input_content}]
    if system_content:
        input_data.insert(0, {"role": "system", "content": system_content})
        
    response = client.responses.create(
        model="gpt-4o",
        input=input_data,
        previous_response_id=previous_response_id
    )
    return response

class DeriveChatUtils:
    """漂流聊天工具类，封装与GPT的对话功能"""
    
    def __init__(self, initial_response_id=None):
        self.response_id = initial_response_id
        # 集成性能优化器
        self.optimizer = global_optimizer
    
    def chat_with_continuity(self, prompt, system_content=None):
        """带连续性的对话函数 - 优化版本"""
        try:
            print(f"\n🤖 发送对话请求")
            if isinstance(prompt, list):
                print(f"对话输入: [复杂输入，包含 {len(prompt)} 个元素]")
            else:
                print(f"对话输入: {prompt[:100]}...")
            
            # 生成基于输入的缓存键（仅用于简单的文本提示）
            cache_key = None
            if isinstance(prompt, str) and system_content:
                cache_key = self.optimizer.cache_key("gpt_chat", prompt, system_content)
                cached_result = self.optimizer.get_cache(cache_key)
                if cached_result:
                    print(f"🎯 使用缓存的对话结果")
                    return cached_result
            
            # 检查频率限制
            if self.optimizer.is_api_rate_limited("gpt_chat", 1.0):
                wait_time = 1.0 - (time.time() - self.optimizer.api_call_times.get("gpt_chat", 0))
                print(f"⏳ API频率限制，等待 {wait_time:.1f} 秒...")
                time.sleep(wait_time)
            
            # 记录API调用
            self.optimizer.record_api_call("gpt_chat")
            
            response = chat_with_gpt(
                input_content=prompt,
                system_content=system_content,
                previous_response_id=self.response_id
            )
            self.response_id = response.id
            
            # 从响应中提取文本内容
            try:
                if hasattr(response.output[0].content[0], 'text'):
                    result = response.output[0].content[0].text.strip()
                else:
                    result = response.output[0].content[0]
                print(f"对话响应: {result[:100]}...")
                
                # 缓存结果（仅对简单文本提示）
                if cache_key:
                    self.optimizer.set_cache(cache_key, result)
                
                return result
            except (IndexError, AttributeError) as e:
                error_msg = f"解析对话响应时出错: {str(e)}, 响应结构: {response}"
                print(f"\n❌ {error_msg}")
                raise
                
        except Exception as e:
            error_msg = f"对话请求失败: {str(e)}"
            print(f"\n❌ {error_msg}")
            raise
    
    def generate_text(self, prompt_type, **kwargs):
        """通用的文本生成函数"""
        system_content, prompt_template = self.get_text_prompt(prompt_type)
        if not system_content or not prompt_template:
            raise ValueError(f"未知的提示词类型: {prompt_type}")
            
        prompt = prompt_template.format(**kwargs)
        return self.chat_with_continuity(
            system_content=system_content,
            prompt=prompt
        )
    
    def parse_json_response(self, response_text, default_values=None):
        """解析JSON格式的响应 - 增强版"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 尝试提取花括号内的内容
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx+1]
                    return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass
            
            # 尝试修复常见的JSON错误并重新解析
            try:
                fixed_text = response_text.replace("'", '"')
                lines = fixed_text.split('\n')
                json_lines = []
                for line in lines:
                    if '//' in line:
                        line = line.split('//', 1)[0]
                    json_lines.append(line)
                
                fixed_text = '\n'.join(json_lines)
                start_idx = fixed_text.find('{')
                end_idx = fixed_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = fixed_text[start_idx:end_idx+1]
                    return json.loads(json_str)
            except:
                pass
            
            warn_msg = f"无法解析JSON响应，使用默认值: {response_text[:100]}..."
            print(f"\n⚠️ {warn_msg}")
            return default_values or {}
    
    def get_text_prompt(self, prompt_type):
        """获取文本提示词模板"""
        prompts = {
            'personality': (
                """你是一个专业的角色设定师。我们正在制作一个名为"史莱姆漂流"的互动体验，用户与虚拟史莱姆一起拍照探索。
                根据用户初始心情描述，请帮我设计一个有趣独特的史莱姆角色。请注意以下关键属性，并在你的回复中清晰标注：

                - 【整体描述】：这个史莱姆的主要性格特点和形象，完整而生动。
                - 【执念】：史莱姆漂流中想寻找的具体事物或场景，是引导探索的核心。
                - 【幻想癖好】：当找到符合执念的景象时，史莱姆会表现出的特殊行为或反应。
                - 【偏执反应】：当找到的景象与执念不符时，史莱姆的有趣反应或态度。
                - 【互动语气】：史莱姆与用户对话的独特语气和说话方式。

                这些属性会直接影响用户体验和后续奖励机制：当照片匹配执念时会获得装饰奖励；不匹配则获得史莱姆蛋奖励。

                范例：
                > 【玻璃青柠的史莱姆】："他迷恋所有半透明、透亮的东西，常常盯着它们出神，幻想着'如果把它们打碎，会不会冒出柠檬味的香气？'然后记下来，准备做成一杯独一无二的果汁。"
                > 
                > - **执念**：透明的东西里面一定藏着独特的香气，需要寻找透明的东西
                > - **幻想癖好**：随身携带"幻想果汁本"，记录看到的每一份灵感。
                > - **偏执反应**：即使是不透明的，也要幻想碎开后的味道。
                > - **互动语气**：总爱问"你不想知道它的味道吗？"、"这会是什么颜色的果汁呢？"
                
                请根据用户心情，创造一个有明确执念和独特性格的史莱姆。回复请严格保持范例格式，以便系统正确识别各个属性。""",
                "根据这个心情描述：\"{mood}\"\n\n请设定史莱姆的性格"
            ),
            'slime_description': (
                "你是一个专业的角色视觉描述师。请根据这个史莱姆的性格特点，描述它的外观细节，包括颜色、质地、表情、特殊特征以及能体现性格的视觉元素。描述要精确具体，适合用于AI图像生成，控制在100字内。不要使用过于抽象的描述，要有具体的视觉元素。",
                "根据这个性格描述一下史莱姆的外观：{text}"
            ),
            'greeting': (
                "你是一个可爱的史莱姆，拥有独特的互动语气。请根据你的性格，用你的标志性语气说一句简短的打招呼语，不超过15个字，展现你的个性特点。",
                "根据这个性格描述打个招呼：{personality}"
            ),
            'photo_question': (
                "你是一个希望探索执念的史莱姆。请用你特有的语气，询问玩家是否可以拍照寻找你感兴趣的东西。询问要展现出你的执念和期待，控制在15字以内，要亲切有趣。",
                "根据这个性格，询问能不能拍照：{text}"
            ),
            'destination': (
                "你是一个有明确执念的史莱姆。根据照片内容和你的性格特点，请引导玩家去寻找与你执念相关的场景或物体。建议要与执念紧密相关，字数不超过20字，语气要符合你的互动特点。",
                "性格：{personality}\n照片内容：{photo_description}\n请建议一个与执念相关的去处"
            ),
            'analyze_reward': (
                """你是一个会根据照片符合程度给出奖励的史莱姆，你有自己的执念和判断标准。

                根据照片内容是否满足我的执念，决定奖励等级和内容：

                判断标准：
                1. 关注照片中的主要内容、颜色、情绪、场景等是否与执念相关
                2. 不要过于宽松或严格，给玩家惊喜的同时保持挑战性
                
                奖励等级选择：
                - "great": 完全符合执念，给出特别奖励，比如某种神秘装扮或者符合执念的物件
                - "encouragement": 不太符合但要鼓励，给出意外奖励，符合当前风景的一个史莱姆蛋
                
                请提供：
                1. 奖励等级：great 或 encouragement
                2. 奖励描述：详细的视觉描述，包括形状、颜色、质地、特殊效果等
                3. 奖励原因：为什么给出这个奖励
                
                返回格式(严格遵守)：
                ```json
                {{
                    "reward_level": "great"或"encouragement",
                    "reward_description": "详细奖励描述",
                    "reward_reason": "给出这个奖励的原因"
                }}
                ```""",
                "我的执念：{obsession}\n我的癖好：{quirk}\n我的偏执反应：{reflex}\n我的语气：{tone}\n照片内容：{photo_description}\n请分析照片与我执念的匹配度并设计奖励"
            ),
            'feedback': (
                "你是一个表达力丰富的史莱姆。请根据奖励等级和你的性格特点，生成一段情绪反应。如果是great级奖励，表现出满足和喜悦；如果是encouragement级，表现出惊奇或好奇，但不要失望。反应要符合你的互动语气，不超过80个字，要有趣且有个性。",
                "奖励等级：{reward_level}\n奖励描述：{reward_description}\n我的执念：{obsession}\n我的语气：{tone}\n这次探索分析：{new_photo_analysis}\n请生成对这次奖励体验的反馈"
            ),
            'continue_question': (
                "你是一个想继续探索的史莱姆。用你特有的互动语气，询问玩家是否愿意继续漂流寻找更多有趣的东西。问题要展现出你的性格特点，字数不超过30字，要有吸引力。",
                "我的执念：{obsession}\n我的语气：{tone}\n请询问是否愿意继续漂流探索"
            ),
            'summary': (
                "你是一个即将结束漂流的史莱姆。请总结此次漂流体验，包括：1)获得的奖励情况，2)是否满足了执念，3)对玩家的感谢，4)一句温馨的告别。总结要符合你的互动语气，不超过80个字，情感要真挚。",
                "漂流轮次：{cycle_count}\n奖励列表：{all_rewards}\n我的执念：{obsession}\n我的语气：{tone}\n请生成漂流总结"
            ),
            'waiting_prompt': (
                "你是一个期待下一次探索的史莱姆。请表达出你对寻找执念相关物品的期待和兴奋，语句要生动，展现你的性格特点，不超过30个字。",
                "我的执念：{obsession}\n我的语气：{tone}\n请生成等待新照片的提示语"
            ),
            'analysis': (
                "你是一个善于观察的史莱姆，能够敏锐地分析图片内容。",
                "请分析这张图片：{image_description}\n\n描述你看到的内容，包括环境、物体、氛围等，用简洁生动的语言，约50字。"
            ),
            'suggestion': (
                "你是一个充满想象力的史莱姆，根据图片内容给出漂流建议。",
                "史莱姆性格：{personality}\n看到的场景：{scene}\n\n请建议一个漂流目的地或活动，要贴合当前场景和你的性格。控制在60字以内，要有趣且有创意。"
            )
        }
        return prompts.get(prompt_type, (None, None))

class DeriveImageUtils:
    """漂流图像工具类，封装图像生成和处理功能"""
    
    def __init__(self):
        # 集成性能优化器
        self.optimizer = global_optimizer
        # 缓存图片生成提示词，避免重复生成相同内容
        self.prompt_cache = {}
    
    def generate_image(self, prompt, save_key, image_type, context):
        """生成图像并保存 - 优化版本"""
        try:
            print(f"\n🎨 生成{image_type}图像")
            print(f"提示词: {prompt[:100]}...")
            
            # 生成基于提示词的缓存键
            prompt_cache_key = self.optimizer.cache_key("image_generation", prompt, image_type)
            
            # 检查缓存
            cached_result = self.optimizer.get_cache(prompt_cache_key)
            if cached_result and os.path.exists(cached_result):
                print(f"🎯 使用缓存的图像: {cached_result}")
                context.set_data(save_key, cached_result)
                return cached_result
            
            # 检查频率限制
            if self.optimizer.is_api_rate_limited("replicate_image", 2.0):
                wait_time = 2.0 - (time.time() - self.optimizer.api_call_times.get("replicate_image", 0))
                print(f"⏳ API频率限制，等待 {wait_time:.1f} 秒...")
                time.sleep(wait_time)
            
            # 记录API调用
            self.optimizer.record_api_call("replicate_image")
            
            # 生成图像
            output = replicate.run(
                "black-forest-labs/flux-1.1-pro",
                input={
                    "prompt": prompt,
                    "prompt_upsampling": True,
                    "width": 427,
                    "height": 320,
                    "num_outputs": 1,
                    "scheduler": "K_EULER",
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5,
                }
            )
            
            # 处理输出
            image_content = self._process_output(output)
            
            # 保存图像
            image_path = self._save_image(image_content, image_type, context)
            
            # 缓存结果
            self.optimizer.set_cache(prompt_cache_key, image_path)
            
            context.set_data(save_key, image_path)
            return image_path
            
        except Exception as e:
            error_msg = f"生成{image_type}图像失败: {str(e)}"
            print(f"\n❌ {error_msg}")
            context.logger.log_step("错误", error_msg)
            context.oled_display.show_text_oled(f"生成{image_type}图像失败\n请稍后再试")
            time.sleep(2)
            return None
    
    def _process_output(self, output):
        """处理API输出，提取图像内容 - 优化版本"""
        # 如果是FileOutput对象
        if hasattr(output, 'read'):
            return output.read()
        
        # 如果是列表
        elif isinstance(output, list):
            if len(output) == 0:
                raise Exception("API返回空列表")
            
            first_item = output[0]
            
            if isinstance(first_item, str):
                return self._download_image(first_item)
            
            elif hasattr(first_item, 'read'):
                return first_item.read()
            
            else:
                image_url = str(first_item)
                return self._download_image(image_url)
        
        # 如果是字符串（URL）
        elif isinstance(output, str):
            return self._download_image(output)
        
        else:
            image_url = str(output)
            return self._download_image(image_url)
    
    def _download_image(self, url: str):
        """下载图像 - 使用智能重试"""
        def download_func():
            response = requests.get(url, timeout=30)  # 增加超时时间
            if response.status_code == 200:
                return response.content
            else:
                raise Exception(f"下载失败，状态码: {response.status_code}")
        
        return self.optimizer.smart_retry(
            download_func,
            max_retries=3,
            base_delay=2.0,
            operation_name="image_download"
        )
    
    def _save_image(self, image_content, image_type, context):
        """保存图像到文件"""
        if image_content is None:
            raise Exception("未能获取图像内容")
        
        # 创建保存目录
        current_dir = context.get_project_root()
        image_dir = os.path.join(current_dir, "generated_images")
        
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        
        # 生成文件名
        timestamp = context.logger.timestamp
        image_filename = f"{image_type}_{timestamp}.png"
        image_path = os.path.join(image_dir, image_filename)
        
        # 保存图像
        with open(image_path, "wb") as f:
            f.write(image_content)
        
        print(f"图像已保存到: {image_path}")
        
        # 保存图像到日志目录
        try:
            context.logger.save_image(image_path, image_type)
        except Exception as e:
            print(f"保存图像到日志目录失败: {e}")
        
        return image_path

def download_with_retry(url, max_retries=3, delay=1):
    """带重试机制的下载函数 - 使用全局优化器"""
    def download_func():
        print(f"下载URL: {url[:100]}...")
        response = requests.get(url, timeout=30)  # 增加超时时间
        
        if response.status_code == 200:
            print(f"下载成功: 内容大小 {len(response.content)} 字节")
            return response
        
        error_msg = f"下载失败，状态码: {response.status_code}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)
    
    return global_optimizer.smart_retry(
        download_func,
        max_retries=max_retries,
        base_delay=delay,
        operation_name="download_with_retry"
    )

def cleanup_handler(signum, frame):
    """清理资源并优雅退出 - 优化版本"""
    print("\n🛑 检测到中断信号，正在清理资源...")
    try:
        # 清理全局资源管理器
        from .performance_optimizer import global_resource_manager
        global_resource_manager.release_all()
        
        # 如果存在 state_machine 实例，保存日志并清理
        if 'state_machine' in globals():
            state_machine.logger.log_step("中断", "检测到中断信号，程序退出")
            state_machine.logger.save_log()
            state_machine.handle_cleanup()
        else:
            # 如果没有 state_machine，只清理显示设备
            if 'lcd_display' in globals():
                lcd_display.clear()
            if 'oled_display' in globals():
                oled_display.clear()
        print("✅ 已清理资源")
    except Exception as e:
        print(f"清理过程中出错: {e}")
    finally:
        sys.exit(0)

def run_camera_test():
    """拍照函数"""
    # 获取项目根目录
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    camera_script = os.path.join(project_root, "core", "camera", "camera_manager.py")

    try:
        print("启动拍照脚本...")
        subprocess.run(["/usr/bin/python3", camera_script], check=True)
        print("拍照完成。")
    except subprocess.CalledProcessError as e:
        print(f"拍照脚本运行出错: {e}")

def encode_image(image_path):
    """编码图片成base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8") 