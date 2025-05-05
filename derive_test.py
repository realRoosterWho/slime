import subprocess
import os
import sys
import base64
import replicate
import requests
import time
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from display_utils import DisplayManager
import signal
import shutil
from button_utils import InputController
from enum import Enum, auto
import RPi.GPIO as GPIO  # 添加这个导入
from PIL import Image
from io import BytesIO

# 加载环境变量
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
replicate_api_key = os.getenv("REPLICATE_API_KEY")

if not replicate_api_key:
    raise Exception("没有找到REPLICATE_API_KEY，请检查.env文件设置！")

replicate_client = replicate.Client(api_token=replicate_api_key)

class DeriveLogger:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.join(self.current_dir, "derives", self.timestamp)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.log_data = {
            "timestamp": self.timestamp,
            "steps": [],
            "images": {},
            "prompts": {},
            "responses": {}
        }
    
    def log_step(self, step_name, message):
        """记录步骤信息"""
        print(f"\n📝 {message}")
        self.log_data["steps"].append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "step": step_name,
            "message": message
        })
        
    def save_image(self, image_path, image_type):
        """保存图片到日志目录"""
        if os.path.exists(image_path):
            filename = os.path.basename(image_path)
            new_path = os.path.join(self.log_dir, filename)
            shutil.copy2(image_path, new_path)
            self.log_data["images"][image_type] = filename
            return new_path
        return None
    
    def log_prompt(self, prompt_type, prompt):
        """记录提示词"""
        self.log_data["prompts"][prompt_type] = prompt
    
    def log_response(self, response_type, response):
        """记录响应"""
        self.log_data["responses"][response_type] = response
    
    def save_log(self):
        """保存日志文件"""
        log_path = os.path.join(self.log_dir, "derive_log.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self.log_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 日志已保存到: {log_path}")

    def get_timestamped_filename(self, original_name, ext):
        """生成带时间戳的文件名"""
        base_name = os.path.splitext(original_name)[0]
        return f"{base_name}_{self.timestamp}{ext}"

def chat_with_gpt(input_content, system_content=None, previous_response_id=None):
    """与GPT进行对话"""
    # 如果输入是列表（包含图片），直接使用
    if isinstance(input_content, list):
        messages = input_content
    else:
        # 否则构建普通文本消息
        messages = [{"type": "input_text", "text": input_content}]
        
    if system_content:
        messages.insert(0, {"type": "input_text", "text": system_content})
        
    response = client.responses.create(
        model="gpt-4o-mini",
        input=messages,
        previous_response_id=previous_response_id
    )
    return response

def run_camera_test():
    """拍照函数"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    camera_script = os.path.join(current_dir, "camera_test.py")

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
        if 'lcd_display' in globals():
            lcd_display.clear()
        if 'oled_display' in globals():
            oled_display.clear()
        print("✅ 已清理显示资源")
    except:
        pass
    sys.exit(0)

def download_with_retry(url, max_retries=3, delay=1):
    """带重试机制的下载函数"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response
            print(f"下载失败，状态码: {response.status_code}，尝试重试...")
        except requests.exceptions.RequestException as e:
            print(f"下载出错 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
                continue
            raise
    return None

class DeriveState(Enum):
    """漂流状态枚举"""
    INIT = auto()                  # 初始化
    GEN_SLIME_IMAGE = auto()       # 生成史莱姆图片
    SHOW_SLIME_IMAGE = auto()      # 显示史莱姆图片
    SHOW_GREETING = auto()         # 显示打招呼
    ASK_PHOTO = auto()            # 询问拍照
    TAKE_PHOTO = auto()           # 拍照
    ANALYZE_PHOTO = auto()        # 分析照片
    SUGGEST_DESTINATION = auto()   # 建议目的地
    CLEANUP = auto()              # 清理
    EXIT = auto()                 # 退出

class DeriveStateMachine:
    def __init__(self, initial_text):
        # 在类初始化时设置 GPIO 模式
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        self.logger = DeriveLogger()
        self.oled_display = DisplayManager("OLED")
        self.lcd_display = DisplayManager("LCD")
        self.controller = InputController()
        self.state = DeriveState.INIT
        self.initial_text = initial_text
        self.response_id = None
        self.data = {
            'personality': None,
            'greeting': None,
            'photo_description': None,
            'destination_suggestion': None,
            'image_path': None,
            'timestamped_image': None,
            'slime_image': None,
            'slime_description': None
        }
        
        # 设置 Replicate API token
        replicate_api_key = os.getenv("REPLICATE_API_KEY")
        if not replicate_api_key:
            raise Exception("没有找到REPLICATE_API_KEY，请检查.env文件设置！")
        os.environ["REPLICATE_API_TOKEN"] = replicate_api_key

    def chat_with_continuity(self, prompt, system_content=None):
        """带连续性的对话函数"""
        response = chat_with_gpt(
            input_content=prompt,  # prompt 可以是文本或包含图片的列表
            system_content=system_content,
            previous_response_id=self.response_id
        )
        self.response_id = response.id  # 保存响应ID以维持对话连续性
        if hasattr(response.output[0].content[0], 'text'):
            return response.output[0].content[0].text.strip()
        return response.output[0].content[0]

    def wait_for_button(self, display_text):
        """等待按钮点击的通用函数"""
        self.oled_display.wait_for_button_with_text(
            self.controller,
            display_text
        )

    def generate_text_prompt(self, prompt_type):
        """生成不同类型文本的提示词模板"""
        prompts = {
            'personality': (
                """你是一个专业的角色设定师。根据环境或物体的描述，帮我设定一只史莱姆的性格特点，用中文简洁描述，不要太长，情感要细腻。以下是你设计角色的一般要求：

                - 【描述（Description）】："史莱姆"的"情绪主题"。每一个史莱姆都是由先前玩家的"漂流"经验中收获的"史莱姆蛋"生成的，玩家在每次漂流前决定了选择带哪一个"史莱姆"进行漂流，这也决定了本次漂流的"主题"。这个属性是决定性的，接下来的属性也是由"描述"这个属性生成的。
                - 【执念（Obsession）】："史莱姆"漂流中的具象目标。根据"史莱姆"的性格，在漂流中"史莱姆"会引导玩家寻找不同的风景，也是提示词的基础设定。
                - 【幻想癖好（Quirk）】：目标达成的正向反馈。如果找到了"合适"的风景，"史莱姆"将会具有的反应。这些奖励与"史莱姆"的"执念"相关，最后会生成"装扮奖励"。
                - 【偏执反应（Reflex）】：目标未达成的意外反馈。如果找到了"不合适"的风景，"史莱姆"会有的反应。这些奖励虽然没办法达成"史莱姆"的执念，但是它仍然会有符合性格的反馈，并且还会生成意外的"史莱姆蛋"奖励。
                - 【互动语气（Interaction Tone）】：根据以上属性生成的互动预期。每次互动不仅有奖励的反馈，还需要有即时的互动反馈。

                以下是具体的例子：

                > 【玻璃青柠的史莱姆】："他迷恋所有半透明、透亮的东西，常常盯着它们出神，幻想着'如果把它们打碎，会不会冒出柠檬味的香气？'然后记下来，准备做成一杯独一无二的果汁。"
                > 
                > - **执念**：透明的东西里面一定藏着独特的香气，需要寻找透明的东西
                > - 幻想**癖好**：随身携带"幻想果汁本"，记录看到的每一份灵感。
                > - 偏执反应：即使是不透明的，也要幻想碎开后的味道。
                > - **互动语气**：总爱问"你不想知道它的味道吗？"、"这会是什么颜色的果汁呢？
                
                现在你已经知道了一般的生成角色的要求，但是你需要根据以下的玩家心情描述来生成一只特殊的史莱姆，这将会在下面的提示词中体现。你的描述方式应该和例子一样。""",
                "根据这个描述设定史莱姆的性格：{text}"
            ),
            'slime_description': (
                "你是一个专业的角色描述师。请根据这个史莱姆的性格特点，描述它的外观、表情、动作等视觉特征，还要有场景的描述，用简短的中文描述，要具体且生动，适合用于图像生成。",
                "根据这个性格描述一下史莱姆的样子：{text}"
            ),
            'greeting': (
                "你是一个可爱的史莱姆。请根据给定的性格描述说一句打招呼的话，中文，不超过15个字。",
                "根据这个性格描述打个招呼：{text}"
            ),
            'photo_question': (
                "你是一个可爱的史莱姆。请用活泼的语气询问是否可以一张风景照，带它去漂流，中文，不超过15个字。",
                "根据这个性格，询问能不能拍照：{text}"
            ),
            'destination': (
                "你是一个可爱的史莱姆。根据照片内容和性格，建议一个去处，中文，不超过20个字。",
                "性格：{personality}\n照片内容：{photo_description}\n请建议一个去处"
            )
        }
        return prompts.get(prompt_type, (None, None))

    def generate_text(self, prompt_type, **kwargs):
        """通用的文本生成函数
        
        Args:
            prompt_type: 提示词类型
            **kwargs: 用于格式化提示词的参数
        Returns:
            生成的文本
        """
        system_content, prompt_template = self.generate_text_prompt(prompt_type)
        if not system_content or not prompt_template:
            raise ValueError(f"未知的提示词类型: {prompt_type}")
            
        prompt = prompt_template.format(**kwargs)
        return self.chat_with_continuity(
            system_content=system_content,
            prompt=prompt
        )

    def handle_init(self):
        """处理初始化状态"""
        self.logger.log_step("初始化", "根据文本开始新的漂流...")
        
        # 使用通用函数生成性格
        self.data['personality'] = self.generate_text('personality', text=self.initial_text)
        self.logger.log_step("性格生成", self.data['personality'])
        
        # 根据性格生成视觉描述
        self.data['slime_description'] = self.generate_text('slime_description', text=self.data['personality'])
        self.logger.log_step("外观描述", self.data['slime_description'])
        
        self.oled_display.show_text_oled("性格设定完成")
        time.sleep(1)

    def generate_image_prompt(self, prompt_type):
        """生成不同类型图片的提示词"""
        prompts = {
            'slime': f"一个奇幻的史莱姆生物。{self.data['slime_description']} 儿童绘本插画风格，色彩丰富且可爱。史莱姆是一个可爱蓬松的生物，有两只大眼睛和一个小嘴巴。",
            # 可以在这里添加其他类型的提示词模板
            'scene': lambda desc: f"一个梦幻的场景。{desc} 儿童绘本风格，色彩丰富。",
            'item': lambda desc: f"一个物品特写。{desc} 儿童绘本风格，细节清晰。"
        }
        
        if callable(prompts.get(prompt_type)):
            return prompts[prompt_type](self.data.get('description', ''))
        return prompts.get(prompt_type, '')

    def generate_image(self, prompt, save_key, filename_prefix):
        """通用的图片生成函数
        
        Args:
            prompt: 生成图片的提示词
            save_key: 保存在self.data中的键名
            filename_prefix: 保存文件的前缀名
        """
        try:
            self.oled_display.show_text_oled("正在生成\n图片...")
            self.logger.log_prompt("image", prompt)
            
            print(f"\n开始生成图片，使用提示词: {prompt}")
            
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
            
            print(f"API 返回类型: {type(output)}")
            print(f"API 返回内容: {output}")
            
            # 获取图片URL
            if isinstance(output, list):
                image_url = output[0]
            elif isinstance(output, str):
                image_url = output
            else:
                image_url = str(output)
                
            print(f"获取到图片URL: {image_url}")
            
            # 下载图片
            response = requests.get(image_url)
            if response.status_code != 200:
                raise Exception(f"下载图片失败，状态码: {response.status_code}")
            
            # 保存图片
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data[save_key] = os.path.join(
                current_dir,
                self.logger.get_timestamped_filename(filename_prefix, ".png")
            )
            
            # 调整图片尺寸并保存
            img = Image.open(BytesIO(response.content))
            resized = img.resize((320, 240), Image.Resampling.LANCZOS)
            resized.save(self.data[save_key])
            
            self.logger.save_image(self.data[save_key], filename_prefix)
            self.logger.log_step("生成图片", f"{filename_prefix}图片生成成功")
            return True
            
        except Exception as e:
            error_msg = f"生成图片时出错: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.logger.log_step("错误", error_msg)
            self.data[save_key] = None
            self.oled_display.show_text_oled("图片生成失败...")
            time.sleep(2)
            return False

    def handle_gen_slime_image(self):
        """处理生成史莱姆图片状态"""
        prompt = self.generate_image_prompt('slime')
        return self.generate_image(prompt, 'slime_image', 'slime')

    def handle_show_slime_image(self):
        """处理显示史莱姆图片状态"""
        if not self.data['slime_image'] or not os.path.exists(self.data['slime_image']):
            self.logger.log_step("显示图片", "跳过图片显示：图片未生成")
            return
            
        try:
            self.oled_display.show_text_oled("史莱姆\n绘制完成！")
            time.sleep(1)
            
            img = Image.open(self.data['slime_image'])
            self.lcd_display.show_image(img)
            self.logger.log_step("显示图片", "史莱姆图片显示成功")
            
            # 等待按钮按下才继续
            self.wait_for_button("按下按钮\n继续...")
            
        except Exception as e:
            error_msg = f"显示图片时出错: {str(e)}"
            print(error_msg)
            self.logger.log_step("错误", error_msg)
            self.oled_display.show_text_oled("图片显示失败...")
            time.sleep(2)

    def handle_show_greeting(self):
        """处理显示打招呼状态"""
        # 使用通用函数生成打招呼语句
        self.data['greeting'] = self.generate_text('greeting', text=self.data['personality'])
        
        self.logger.log_step("打招呼", self.data['greeting'])
        self.wait_for_button(f"史莱姆说：\n{self.data['greeting']}")

    def handle_ask_photo(self):
        """处理询问拍照状态"""
        # 使用通用函数生成询问语句
        photo_question = self.generate_text('photo_question', text=self.data['personality'])
        
        self.logger.log_step("询问拍照", photo_question)
        self.wait_for_button(f"史莱姆说：\n{photo_question}")

    def handle_take_photo(self):
        """处理拍照状态"""
        self.oled_display.show_text_oled("准备拍照...")
        run_camera_test()
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        original_image = os.path.join(current_dir, "current_image.jpg")
        self.data['timestamped_image'] = os.path.join(
            current_dir, 
            self.logger.get_timestamped_filename("current_image", ".jpg")
        )
        shutil.copy2(original_image, self.data['timestamped_image'])
        self.logger.save_image(self.data['timestamped_image'], "original")

    def handle_analyze_photo(self):
        """处理分析照片状态"""
        self.oled_display.show_text_oled("正在分析\n照片...")
        
        base64_image = encode_image(self.data['timestamped_image'])
        data_url = f"data:image/jpeg;base64,{base64_image}"
        
        # 修改输入格式
        input_content = [
            {"type": "input_text", "text": "请简短描述这张照片的主要内容。"},
            {"type": "input_image", "image_url": data_url}
        ]
        
        # 使用修改后的 chat_with_continuity
        response = self.chat_with_continuity(input_content)
        
        # 确保我们正确获取响应文本
        if hasattr(response.output[0].content[0], 'text'):
            self.data['photo_description'] = response.output[0].content[0].text.strip()
        else:
            self.data['photo_description'] = response.output[0].content[0]
        
        self.logger.log_step("照片分析", self.data['photo_description'])
        self.wait_for_button(f"分析结果：\n{self.data['photo_description']}")

    def handle_suggest_destination(self):
        """处理建议目的地状态"""
        # 使用通用函数生成建议
        suggestion = self.generate_text(
            'destination',
            personality=self.data['personality'],
            photo_description=self.data['photo_description']
        )
        
        self.logger.log_step("建议目的地", suggestion)
        self.wait_for_button(f"史莱姆说：\n{suggestion}")

    def handle_cleanup(self):
        """处理清理状态"""
        try:
            self.controller.cleanup()
            self.lcd_display.clear()
            self.oled_display.clear()
            self.logger.save_log()
        finally:
            GPIO.cleanup()  # 确保在最后清理 GPIO
        return
    
    def run(self):
        """运行状态机"""
        state_transitions = {
            DeriveState.INIT: DeriveState.GEN_SLIME_IMAGE,
            DeriveState.GEN_SLIME_IMAGE: DeriveState.SHOW_SLIME_IMAGE,
            DeriveState.SHOW_SLIME_IMAGE: DeriveState.SHOW_GREETING,
            DeriveState.SHOW_GREETING: DeriveState.ASK_PHOTO,
            DeriveState.ASK_PHOTO: DeriveState.TAKE_PHOTO,
            DeriveState.TAKE_PHOTO: DeriveState.ANALYZE_PHOTO,
            DeriveState.ANALYZE_PHOTO: DeriveState.SUGGEST_DESTINATION,
            DeriveState.SUGGEST_DESTINATION: DeriveState.CLEANUP,
            DeriveState.CLEANUP: DeriveState.EXIT
        }
        
        state_handlers = {
            DeriveState.INIT: self.handle_init,
            DeriveState.GEN_SLIME_IMAGE: self.handle_gen_slime_image,
            DeriveState.SHOW_SLIME_IMAGE: self.handle_show_slime_image,
            DeriveState.SHOW_GREETING: self.handle_show_greeting,
            DeriveState.ASK_PHOTO: self.handle_ask_photo,
            DeriveState.TAKE_PHOTO: self.handle_take_photo,
            DeriveState.ANALYZE_PHOTO: self.handle_analyze_photo,
            DeriveState.SUGGEST_DESTINATION: self.handle_suggest_destination,
            DeriveState.CLEANUP: self.handle_cleanup
        }
        
        try:
            while self.state != DeriveState.EXIT:
                handler = state_handlers.get(self.state)
                if handler:
                    handler()
                    self.state = state_transitions.get(self.state, DeriveState.CLEANUP)
                else:
                    raise ValueError(f"未知状态: {self.state}")
                    
        except Exception as e:
            self.logger.log_step("错误", f"程序运行出错: {str(e)}")
            self.state = DeriveState.CLEANUP
            self.handle_cleanup()

def main():
    # 设置信号处理
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # 这里需要传入初始文本
    initial_text = "今天我心情有点不好，我有点忧郁。你能带我在这个氛围里面漂流吗？"  # 这里替换为实际的输入文本
    
    # 运行状态机
    state_machine = DeriveStateMachine(initial_text)
    state_machine.run()

if __name__ == "__main__":
    main() 