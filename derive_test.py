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
    input_data = [{"role": "user", "content": input_content}]
    if system_content:
        input_data.insert(0, {"role": "system", "content": system_content})
        
    response = client.responses.create(
        model="gpt-4o-mini",
        input=input_data,
        previous_response_id=None
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
    INIT = auto()          # 初始化
    TAKE_PHOTO = auto()    # 拍照
    ANALYZE_PHOTO = auto() # 分析照片
    SHOW_ANALYSIS = auto() # 显示分析结果
    GEN_PERSONALITY = auto() # 生成性格
    SHOW_PERSONALITY = auto() # 显示性格
    GEN_GREETING = auto()  # 生成问候
    SHOW_GREETING = auto() # 显示问候
    GEN_IMAGE = auto()     # 生成图片
    SHOW_IMAGE = auto()    # 显示图片
    CLEANUP = auto()       # 清理
    EXIT = auto()          # 退出

class DeriveStateMachine:
    def __init__(self):
        # 初始化 GPIO 模式
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        self.logger = DeriveLogger()
        self.oled_display = DisplayManager("OLED")
        self.lcd_display = DisplayManager("LCD")
        self.controller = InputController()
        self.state = DeriveState.INIT
        self.data = {
            'description': None,
            'personality': None,
            'greeting': None,
            'image_path': None,
            'timestamped_image': None
        }
    
    def handle_init(self):
        """处理初始化状态"""
        self.logger.log_step("初始化", "开始新的漂流...")
        self.oled_display.show_text_oled("初始化完成")
        time.sleep(1)
    
    def handle_take_photo(self):
        """处理拍照状态"""
        self.oled_display.show_text_oled("准备拍照...")
        run_camera_test()
        
        # 保存带时间戳的照片
        current_dir = os.path.dirname(os.path.abspath(__file__))
        original_image = os.path.join(current_dir, "current_image.jpg")
        self.data['timestamped_image'] = os.path.join(
            current_dir, 
            self.logger.get_timestamped_filename("current_image", ".jpg")
        )
        shutil.copy2(original_image, self.data['timestamped_image'])
        self.logger.save_image(self.data['timestamped_image'], "original")
    
    def handle_analyze_photo(self):
        """处理照片分析状态"""
        self.oled_display.show_text_oled("正在分析\n图片...")
        base64_image = encode_image(self.data['timestamped_image'])
        data_url = f"data:image/jpeg;base64,{base64_image}"
        
        response = chat_with_gpt(
            input_content=[
                {"type": "input_text", "text": "请简短描述这张照片的主要内容。"},
                {"type": "input_image", "image_url": data_url}
            ]
        )
        self.data['description'] = response.output[0].content[0].text.strip()
        self.logger.log_response("image_description", self.data['description'])
        
    def handle_show_analysis(self):
        """处理显示分析结果状态"""
        self.oled_display.wait_for_button_with_text(
            self.controller, 
            f"识别结果:\n{self.data['description']}"
        )
    
    def handle_gen_personality(self):
        """处理生成性格状态"""
        self.oled_display.show_text_oled("正在生成\n史莱姆性格...")
        personality_prompt = f"根据这个描述设定一只史莱姆：{self.data['description']}"
        self.logger.log_prompt("personality", personality_prompt)
        
        response = chat_with_gpt(
            system_content="你是一个专业的角色设定师。根据环境或物体的描述，帮我设定一只史莱姆的小档案，包括它的性格、表情、动作特点等，用中文简洁描述，不要太长，情感要细腻。",
            input_content=personality_prompt
        )
        self.data['personality'] = response.output[0].content[0].text.strip()
        self.logger.log_response("personality", self.data['personality'])
        
    def handle_show_personality(self):
        """处理显示性格状态"""
        self.oled_display.wait_for_button_with_text(
            self.controller,
            f"史莱姆性格:\n{self.data['personality']}"
        )
    
    def handle_gen_greeting(self):
        """处理生成问候状态"""
        self.oled_display.show_text_oled("正在想打招呼\n的话...")
        greeting_prompt = f"根据这个性格描述生成打招呼用语：{self.data['personality']}"
        self.logger.log_prompt("greeting", greeting_prompt)
        
        response = chat_with_gpt(
            system_content="你是一个可爱的史莱姆。请根据给定的性格描述说话，中文，不超过15个字。",
            input_content=greeting_prompt
        )
        self.data['greeting'] = response.output[0].content[0].text.strip()
        self.logger.log_response("greeting", self.data['greeting'])
        
    def handle_show_greeting(self):
        """处理显示问候状态"""
        self.oled_display.show_text_oled(self.data['greeting'])
        time.sleep(3)
    
    def handle_gen_image(self):
        """处理生成图片状态"""
        self.oled_display.show_text_oled("正在绘制\n史莱姆...")
        slime_prompt = f"一个奇幻的史莱姆生物。{self.data['personality']} 儿童绘本插画风格，色彩丰富且可爱。史莱姆是一个可爱蓬松的生物，有两只大眼睛和一个小嘴巴。"
        self.logger.log_prompt("image", slime_prompt)
        
        output = replicate_client.run(
            "black-forest-labs/flux-1.1-pro",
            input={
                "prompt": slime_prompt,
                "prompt_upsampling": True,
                "width": 384,        # 使用更大的尺寸，保持 4:3 比例
                "height": 256,       # 满足最小高度要求
                "num_inference_steps": 4
            }
        )
        
        if isinstance(output, list) and len(output) > 0:
            image_url = output[0]
            img_response = download_with_retry(image_url)
            if img_response:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                self.data['image_path'] = os.path.join(current_dir, "new_slime.png")
                
                # 保存原始图片
                with open(self.data['image_path'], "wb") as f:
                    f.write(img_response.content)
                
                # 调整图片大小为 320x240
                img = Image.open(BytesIO(img_response.content))
                resized_img = img.resize((320, 240), Image.Resampling.LANCZOS)
                resized_img.save(self.data['image_path'])
                
                self.logger.save_image(self.data['image_path'], "generated")
                return
        
        return
    
    def handle_show_image(self):
        """处理显示图片状态"""
        self.oled_display.show_text_oled("史莱姆\n绘制完成！")
        time.sleep(1)
        self.lcd_display.show_image(self.data['image_path'])
        time.sleep(60)
    
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
        # 定义状态转换规则
        state_transitions = {
            DeriveState.INIT: DeriveState.TAKE_PHOTO,
            DeriveState.TAKE_PHOTO: DeriveState.ANALYZE_PHOTO,
            DeriveState.ANALYZE_PHOTO: DeriveState.SHOW_ANALYSIS,
            DeriveState.SHOW_ANALYSIS: DeriveState.GEN_PERSONALITY,
            DeriveState.GEN_PERSONALITY: DeriveState.SHOW_PERSONALITY,
            DeriveState.SHOW_PERSONALITY: DeriveState.GEN_GREETING,
            DeriveState.GEN_GREETING: DeriveState.SHOW_GREETING,
            DeriveState.SHOW_GREETING: DeriveState.GEN_IMAGE,
            DeriveState.GEN_IMAGE: DeriveState.SHOW_IMAGE,
            DeriveState.SHOW_IMAGE: DeriveState.CLEANUP,
            DeriveState.CLEANUP: DeriveState.EXIT
        }
        
        # 状态处理函数映射
        state_handlers = {
            DeriveState.INIT: self.handle_init,
            DeriveState.TAKE_PHOTO: self.handle_take_photo,
            DeriveState.ANALYZE_PHOTO: self.handle_analyze_photo,
            DeriveState.SHOW_ANALYSIS: self.handle_show_analysis,
            DeriveState.GEN_PERSONALITY: self.handle_gen_personality,
            DeriveState.SHOW_PERSONALITY: self.handle_show_personality,
            DeriveState.GEN_GREETING: self.handle_gen_greeting,
            DeriveState.SHOW_GREETING: self.handle_show_greeting,
            DeriveState.GEN_IMAGE: self.handle_gen_image,
            DeriveState.SHOW_IMAGE: self.handle_show_image,
            DeriveState.CLEANUP: self.handle_cleanup
        }
        
        try:
            while self.state != DeriveState.EXIT:
                # 获取并执行当前状态的处理函数
                handler = state_handlers.get(self.state)
                if handler:
                    handler()
                    # 获取下一个状态
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
    
    # 运行状态机
    state_machine = DeriveStateMachine()
    state_machine.run()

if __name__ == "__main__":
    main() 