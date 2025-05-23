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

# 加载环境变量
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    
    def chat_with_continuity(self, prompt, system_content=None):
        """带连续性的对话函数"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"\n🤖 发送对话请求 (尝试 {attempt+1}/{max_retries})")
                if isinstance(prompt, list):
                    print(f"对话输入: [复杂输入，包含 {len(prompt)} 个元素]")
                else:
                    print(f"对话输入: {prompt[:100]}...")
                
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
                    return result
                except (IndexError, AttributeError) as e:
                    error_msg = f"解析对话响应时出错: {str(e)}, 响应结构: {response}"
                    print(f"\n❌ {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    raise
            except Exception as e:
                error_msg = f"对话请求失败 (尝试 {attempt+1}/{max_retries}): {str(e)}"
                print(f"\n❌ {error_msg}")
                import traceback
                traceback.print_exc()
                
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
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
        """解析JSON格式的响应"""
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
        """生成不同类型文本的提示词模板"""
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
                "根据这个描述设定史莱姆的性格：{text}"
            ),
            'slime_description': (
                "你是一个专业的角色视觉描述师。请根据这个史莱姆的性格特点，描述它的外观细节，包括颜色、质地、表情、特殊特征以及能体现性格的视觉元素。描述要精确具体，适合用于AI图像生成，控制在100字内。不要使用过于抽象的描述，要有具体的视觉元素。",
                "根据这个性格描述一下史莱姆的外观：{text}"
            ),
            'greeting': (
                "你是一个可爱的史莱姆，拥有独特的互动语气。请根据你的性格，用你的标志性语气说一句简短的打招呼语，不超过15个字，展现你的个性特点。",
                "根据这个性格描述打个招呼：{text}"
            ),
            'photo_question': (
                "你是一个希望探索执念的史莱姆。请用你特有的语气，询问玩家是否可以拍照寻找你感兴趣的东西。询问要展现出你的执念和期待，控制在15字以内，要亲切有趣。",
                "根据这个性格，询问能不能拍照：{text}"
            )
        }
        
        return prompts.get(prompt_type, (None, None))

class DeriveImageUtils:
    """漂流图像工具类，封装图像生成和处理功能"""
    
    def __init__(self):
        # 设置 Replicate API
        replicate_api_key = os.getenv("REPLICATE_API_KEY")
        if not replicate_api_key:
            raise Exception("没有找到REPLICATE_API_KEY，请检查.env文件设置！")
        self.replicate_client = replicate.Client(api_token=replicate_api_key)
    
    def generate_image(self, prompt, save_key, image_type, context):
        """生成图像并保存"""
        try:
            # 显示正在生成图像的信息
            context.oled_display.show_text_oled(f"正在生成{image_type}图像...")
            
            # 使用Replicate API生成图像
            output = self.replicate_client.run(
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
            
            if not output:
                raise Exception("未能生成图像")
            
            # 处理不同类型的返回值
            image_content = self._process_output(output)
            
            if image_content is None:
                raise Exception("未能获取图像内容")
                
            # 保存图像
            image_path = self._save_image(image_content, image_type, context)
            
            # 显示生成的图像
            img = Image.open(image_path)
            max_size = (320, 240)
            img.thumbnail(max_size, Image.LANCZOS)
            context.lcd_display.show_image(img)
            
            context.logger.log_step("图像生成", f"{image_type}图像已生成并保存: {image_path}")
            
            return image_path
        except Exception as e:
            error_msg = f"生成{image_type}图像失败: {str(e)}"
            print(f"\n❌ {error_msg}")
            context.logger.log_step("错误", error_msg)
            context.oled_display.show_text_oled(f"生成{image_type}图像失败\n请稍后再试")
            time.sleep(2)
            return None
    
    def _process_output(self, output):
        """处理API输出，提取图像内容"""
        # 如果是FileOutput对象
        if hasattr(output, 'read'):
            return output.read()
        
        # 如果是列表
        elif isinstance(output, list):
            if len(output) == 0:
                raise Exception("API返回空列表")
            
            first_item = output[0]
            
            if isinstance(first_item, str):
                response = download_with_retry(first_item)
                if response is None:
                    raise Exception("无法下载生成的图像")
                return response.content
            
            elif hasattr(first_item, 'read'):
                return first_item.read()
            
            else:
                image_url = str(first_item)
                response = download_with_retry(image_url)
                if response is None:
                    raise Exception("无法下载生成的图像")
                return response.content
        
        # 如果是字符串（URL）
        elif isinstance(output, str):
            response = download_with_retry(output)
            if response is None:
                raise Exception("无法下载生成的图像")
            return response.content
        
        else:
            image_url = str(output)
            response = download_with_retry(image_url)
            if response is None:
                raise Exception("无法下载生成的图像")
            return response.content
    
    def _save_image(self, image_content, image_type, context):
        """保存图像到文件"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_dir = os.path.join(current_dir, "generated_images")
        
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
            
        timestamp = context.logger.timestamp
        image_filename = f"{image_type}_{timestamp}.png"
        image_path = os.path.join(image_dir, image_filename)
        
        with open(image_path, "wb") as f:
            f.write(image_content)
            
        print(f"图像已保存到: {image_path}")
        
        # 保存图像到日志目录
        context.logger.save_image(image_path, image_type)
        
        return image_path

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

def cleanup_handler(signum, frame):
    """清理资源并优雅退出"""
    print("\n🛑 检测到中断信号，正在清理资源...")
    try:
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

def download_with_retry(url, max_retries=3, delay=1):
    """带重试机制的下载函数"""
    for attempt in range(max_retries):
        try:
            print(f"下载URL (尝试 {attempt+1}/{max_retries}): {url[:100]}...")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"下载成功: 内容大小 {len(response.content)} 字节")
                return response
            
            error_msg = f"下载失败，状态码: {response.status_code}, 响应: {response.text[:200]}..."
            print(f"❌ {error_msg}")
            
            if attempt < max_retries - 1:
                print(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
                continue
        except requests.exceptions.RequestException as e:
            error_msg = f"下载请求异常 (尝试 {attempt+1}/{max_retries}): {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            if attempt < max_retries - 1:
                print(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
                continue
    
    print("所有下载尝试均失败")
    return None 