import subprocess
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import base64
import replicate
import requests
import time
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from core.display.display_utils import DisplayManager
import signal
import shutil
from core.input.button_utils import InputController
from enum import Enum, auto
import RPi.GPIO as GPIO
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
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.join(project_root, "derives", self.timestamp)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.log_data = {
            "timestamp": self.timestamp,
            "steps": [],
            "images": {},
            "prompts": {},
            "responses": {}
        }
    
    def log_step(self, step_name, message):
        """记录步骤信息并立即保存日志"""
        print(f"\n📝 {message}")
        self.log_data["steps"].append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "step": step_name,
            "message": message
        })
        # 每记录一步就立即保存日志，防止断电丢失数据
        self.save_log()
        
    def save_image(self, image_path, image_type):
        """保存图片到日志目录"""
        if os.path.exists(image_path):
            filename = os.path.basename(image_path)
            new_path = os.path.join(self.log_dir, filename)
            shutil.copy2(image_path, new_path)
            self.log_data["images"][image_type] = filename
            # 每保存一张图片就立即保存日志
            self.save_log()
            return new_path
        return None
    
    def log_prompt(self, prompt_type, prompt):
        """记录提示词并立即保存日志"""
        self.log_data["prompts"][prompt_type] = prompt
        self.save_log()
    
    def log_response(self, response_type, response):
        """记录响应并立即保存日志"""
        self.log_data["responses"][response_type] = response
        self.save_log()
    
    def save_log(self):
        """保存日志文件"""
        try:
            log_path = os.path.join(self.log_dir, "derive_log.json")
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(self.log_data, f, ensure_ascii=False, indent=2)
            # print(f"✅ 日志已保存到: {log_path}")  # 注释掉频繁的输出
        except Exception as e:
            print(f"⚠️ 保存日志时出错: {e}")

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
        model="gpt-4o",
        input=input_data,
        previous_response_id=previous_response_id
    )
    return response

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
            traceback.print_exc()  # 打印堆栈
            
            if attempt < max_retries - 1:
                print(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
                continue
    
    print("所有下载尝试均失败")
    return None

class DeriveState(Enum):
    """漂流状态枚举"""
    INIT = auto()                  # 初始化
    GEN_SLIME_IMAGE = auto()       # 生成史莱姆图片
    SHOW_SLIME_IMAGE = auto()      # 显示史莱姆图片
    SHOW_GREETING = auto()         # 显示打招呼
    ASK_PHOTO = auto()             # 询问拍照
    TAKE_PHOTO = auto()            # 拍照
    ANALYZE_PHOTO = auto()         # 分析照片
    SUGGEST_DESTINATION = auto()   # 建议目的地
    WAIT_FOR_NEW_PHOTO = auto()    # 等待新的照片
    TAKE_NEW_PHOTO = auto()        # 拍摄新的照片
    ANALYZE_NEW_PHOTO = auto()     # 分析新的照片
    ANALYZE_REWARD = auto()        # 分析奖励
    GENERATE_REWARD_IMAGE = auto() # 生成奖励图片
    SHOW_REWARD = auto()           # 显示奖励
    GENERATE_FEEDBACK = auto()     # 生成反馈
    SHOW_FEEDBACK = auto()         # 显示反馈
    ASK_CONTINUE = auto()          # 询问是否继续
    SUMMARY = auto()               # 总结
    CLEANUP = auto()               # 清理
    EXIT = auto()                  # 退出

class DeriveStateMachine:
    def __init__(self, initial_text):
        # 初始化 GPIO 设置
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        self.logger = DeriveLogger()
        self.oled_display = DisplayManager("OLED")
        self.lcd_display = DisplayManager("LCD")
        self.controller = InputController()
        self.state = DeriveState.INIT
        self.initial_text = initial_text
        self.response_id = None
        
        # 添加按钮2长按检测相关变量
        self.btn2_pressed_time = 0  # 按钮2按下的时间
        self.btn2_state = 1  # 按钮2的初始状态（1表示未按下）
        self.btn2_long_press_threshold = 2.0  # 长按阈值（秒）
        self.return_to_menu = False  # 返回菜单的标志
        
        # 缓存项目根目录路径
        self._project_root = None
        
        self.data = {
            'personality': None,
            'greeting': None,
            'photo_description': None,
            'destination_suggestion': None,
            'image_path': None,
            'timestamped_image': None,
            'slime_image': None,
            'slime_description': None,
            'slime_appearance': None,  # 新增：保存史莱姆外观的详细描述，用于保持一致性
            # 新增数据项，用于后续流程
            'new_photo_description': None,
            'is_obsession_matched': None,
            'reward_type': None,  # 'accessory' 或 'egg'
            'reward_description': None,
            'reward_text': None,
            'reward_image': None,
            'feedback_text': None,
            'feedback_description': None,
            'feedback_image': None,
            'continue_derive': None,
            'summary': None,
            'cycle_count': 0,  # 记录漂流循环次数
            'all_rewards': [],  # 记录所有奖励
            'slime_attributes': {  # 分解的史莱姆属性
                'obsession': None,   # 执念
                'quirk': None,       # 癖好
                'reflex': None,      # 偏执反应
                'tone': None         # 互动语气
            }
        }
        
        # 设置 Replicate API token
        replicate_api_key = os.getenv("REPLICATE_API_KEY")
        if not replicate_api_key:
            raise Exception("没有找到REPLICATE_API_KEY，请检查.env文件设置！")
        os.environ["REPLICATE_API_TOKEN"] = replicate_api_key

    def get_default_slime_attributes(self):
        """获取默认的史莱姆属性值"""
        return {
            'obsession': '寻找美丽和独特的事物',
            'quirk': '兴奋地跳跃并记录下来',
            'reflex': '好奇地观察并寻找其他有趣的特点',
            'tone': '友好热情，充满好奇'
        }

    def get_project_root(self):
        """获取项目根目录路径（缓存版本）"""
        if self._project_root is None:
            self._project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return self._project_root

    def handle_error(self, error_msg, display_msg=None, step_name="错误"):
        """统一的错误处理方法"""
        print(f"\n❌ {error_msg}")
        self.logger.log_step(step_name, error_msg)
        if display_msg:
            self.oled_display.show_text_oled(display_msg)
            time.sleep(2)

    def create_timestamped_filename(self, base_filename, suffix=""):
        """创建带时间戳的文件名"""
        name, ext = os.path.splitext(base_filename)
        if suffix:
            return f"{name}_{suffix}_{self.logger.timestamp}{ext}"
        else:
            return f"{name}_{self.logger.timestamp}{ext}"

    def generate_image_with_retry(self, prompt, save_key, image_type, max_retries=2):
        """带重试机制的图像生成方法"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.oled_display.show_text_oled(f"重试生成\n{image_type}...")
                
                image_path = self.generate_image(prompt, save_key, image_type)
                
                if image_path and os.path.exists(image_path):
                    self.logger.log_step(f"生成{image_type}", f"{image_type}图片已生成: {image_path}")
                    return image_path
                else:
                    if attempt < max_retries - 1:
                        self.handle_error(f"{image_type}图片生成失败，准备重试", f"生成{image_type}失败\n准备重试...")
                    else:
                        raise Exception(f"{image_type}图片生成重试失败")
            except Exception as e:
                if attempt < max_retries - 1:
                    self.handle_error(f"{image_type}图片生成出错: {str(e)}", f"生成{image_type}出错\n准备重试...")
                else:
                    self.handle_error(f"{image_type}图片生成重试失败: {str(e)}", f"生成{image_type}失败\n请稍后再试")
                    raise
        return None

    def display_image_with_text(self, image_key, text, button_text="按下按钮继续", log_success_msg=None, skip_msg=None):
        """统一的图片显示方法"""
        if not self.data.get(image_key) or not os.path.exists(self.data[image_key]):
            if skip_msg:
                self.logger.log_step("显示图片", skip_msg)
            return
            
        try:
            # 显示文本
            self.oled_display.show_text_oled(text)
            time.sleep(1)
            
            # 显示图片
            img = Image.open(self.data[image_key])
            self.lcd_display.show_image(img)
            
            if log_success_msg:
                self.logger.log_step("显示图片", log_success_msg)
            
            # 等待按钮按下 - 只显示简短的按钮提示，避免重复显示长文本
            self.wait_for_button(button_text)
            
        except Exception as e:
            self.handle_error(f"显示图片时出错: {str(e)}", "图片显示失败...")

    def save_photo_with_timestamp(self, photo_path, is_new_photo=False):
        """保存带时间戳的照片副本"""
        filename = os.path.basename(photo_path)
        suffix = "new" if is_new_photo else ""
        timestamped_filename = self.create_timestamped_filename(filename, suffix)
        timestamped_path = os.path.join(self.get_project_root(), timestamped_filename)
        
        # 复制照片
        shutil.copy2(photo_path, timestamped_path)
        
        # 保存到相应的数据键
        if is_new_photo:
            self.data['new_image_path'] = photo_path
            self.data['new_timestamped_image'] = timestamped_path
            self.logger.save_image(timestamped_path, 'new_photo')
            return 'new_timestamped_image'
        else:
            self.data['image_path'] = photo_path
            self.data['timestamped_image'] = timestamped_path
            self.logger.save_image(timestamped_path, 'original_photo')
            return 'timestamped_image'

    def chat_with_continuity(self, prompt, system_content=None):
        """带连续性的对话函数 - 增强版"""
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
                    self.logger.log_step("错误", error_msg)
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    raise
            except Exception as e:
                error_msg = f"对话请求失败 (尝试 {attempt+1}/{max_retries}): {str(e)}"
                print(f"\n❌ {error_msg}")
                import traceback
                traceback.print_exc()  # 打印完整的堆栈跟踪
                self.logger.log_step("错误", error_msg)
                
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise  # 所有重试失败，抛出异常

    def wait_for_button(self, display_text):
        """等待按钮点击的通用函数"""
        self.oled_display.wait_for_button_with_text(
            self.controller,
            display_text
        )

    def generate_text_prompt(self, prompt_type):
        """生成不同类型文本的提示词模板 - 优化后的版本"""
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
            ),
            'destination': (
                "你是一个有明确执念的史莱姆。根据照片内容和你的性格特点，请引导玩家去寻找与你执念相关的场景或物体。建议要与执念紧密相关，字数不超过20字，语气要符合你的互动特点。",
                "性格：{personality}\n照片内容：{photo_description}\n请建议一个与执念相关的去处"
            ),
            'analyze_reward': (
                """你是一个奖励设计专家。请分析照片内容是否满足史莱姆的执念，并设计相应奖励。

                判断标准：
                1. 关注照片中的主要内容、颜色、情绪、场景等是否与执念相关
                2. 不要过于宽松或严格，给玩家惊喜的同时保持挑战性
                
                奖励设计：
                - 若匹配执念：设计一个与史莱姆癖好相关的"装饰物"，如特殊帽子、眼镜、背包等
                - 若不匹配：设计一个与照片内容和史莱姆偏执反应相关的"史莱姆蛋"
                
                请提供：
                1. 奖励描述：详细的视觉描述，包括形状、颜色、质地、特殊效果等
                2. 奖励文本：简短介绍，不超过15字
                
                返回格式(严格遵守)：            ```json
                {
                    "is_matched": true或false,
                    "reward_type": "accessory"或"egg",
                    "reward_description": "详细视觉描述",
                    "reward_text": "简短奖励名称"
                }            ```""",
                "性格：{personality}\n执念：{obsession}\n癖好：{quirk}\n偏执反应：{reflex}\n照片内容：{photo_description}\n请分析照片与执念的匹配度并设计奖励"
            ),
            'feedback': (
                "你是一个表达力丰富的史莱姆。请根据奖励结果（是否符合执念）和你的性格特点，生成一段情绪反应。如果奖励符合执念，表现出满足和喜悦；如果不符合，表现出惊奇或好奇，但不要失望。反应要符合你的互动语气，不超过20个字。",
                "奖励符合执念：{is_matched}\n奖励类型：{reward_type}\n奖励内容：{reward_text}\n性格：{personality}\n互动语气：{tone}\n请生成反应"
            ),
            'continue_question': (
                "你是一个想继续探索的史莱姆。用你特有的互动语气，询问玩家是否愿意继续漂流寻找更多有趣的东西。问题要展现出你的性格特点，字数不超过20字，要有吸引力。",
                "根据史莱姆的性格和互动语气：{tone}，询问是否继续漂流"
            ),
            'summary': (
                "你是一个即将结束漂流的史莱姆。请总结此次漂流体验，包括：1)获得的奖励，2)是否满足了执念，3)对玩家的感谢，4)一句温馨的告别。总结要符合你的互动语气，不超过50个字，情感要真挚。",
                "漂流次数：{cycle_count}\n奖励列表：{rewards}\n性格：{personality}\n互动语气：{tone}\n请生成漂流总结"
            ),
            'waiting_prompt': (
                "你是一个期待下一次探索的史莱姆。请表达出你对寻找执念相关物品的期待和兴奋，语句要生动，展现你的性格特点，不超过20个字。",
                "执念：{obsession}\n互动语气：{tone}\n请生成等待拍照的提示语"
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
        
        # 提取史莱姆属性
        self.extract_slime_attributes(self.data['personality'])
        
        # 根据性格生成视觉描述
        self.data['slime_description'] = self.generate_text('slime_description', text=self.data['personality'])
        self.logger.log_step("外观描述", self.data['slime_description'])
        
        # 保存详细的外观描述用于保持一致性
        self.data['slime_appearance'] = f"一个可爱的史莱姆生物。{self.data['slime_description']} 。"
        self.logger.log_step("一致性外观描述", self.data['slime_appearance'])
        
        self.oled_display.show_text_oled("性格设定完成")
        time.sleep(1)

    def generate_image_prompt(self, prompt_type):
        """生成不同类型图片的提示词"""
        prompts = {
            'slime': f"一个奇幻的史莱姆生物。{self.data['slime_description']} 儿童绘本插画风格，色彩丰富且可爱。史莱姆是一个可爱蓬松的生物，有两只大眼睛和一个小嘴巴。",
            'reward': f"一个奇幻的奖励物品。{self.data['reward_description']} 儿童绘本风格，色彩丰富，特写镜头。",
            'feedback': f"一个史莱姆的情绪反应。{self.data['slime_appearance']} 表情生动，{self.data['feedback_description']} 儿童绘本风格，色彩鲜艳可爱。" 
        }
        
        return prompts.get(prompt_type, '')

    def generate_image(self, prompt, save_key, image_type):
        """生成图像并保存"""
        try:
            # 显示正在生成图像的信息
            self.oled_display.show_text_oled(f"正在生成{image_type}图像...")
            
            # 使用Replicate API生成图像
            output = replicate_client.run(
                "black-forest-labs/flux-1.1-pro",
                input={
                    "prompt": prompt,
                    "prompt_upsampling": True,
                    "width": 427,      # 按比例调整：320/240 * 320 ≈ 427
                    "height": 320,     # 使用允许的最小值的稍大值
                    "num_outputs": 1,
                    "scheduler": "K_EULER",
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5,
                }
            )
            
            # 确保输出是有效的
            if not output:
                raise Exception("未能生成图像")
            
            # 打印调试信息
            print(f"API 返回类型: {type(output)}")
            print(f"API 返回内容: {output}")
            
            # 处理不同类型的返回值
            image_content = None
            
            # 如果是FileOutput对象
            if hasattr(output, 'read'):
                print("检测到FileOutput对象，使用read()方法读取")
                image_content = output.read()
                
            # 如果是列表
            elif isinstance(output, list):
                if len(output) == 0:
                    raise Exception("API返回空列表")
                    
                first_item = output[0]
                
                # 列表中的元素可能是URL字符串
                if isinstance(first_item, str):
                    print(f"从列表中获取URL: {first_item}")
                    response = download_with_retry(first_item)
                    if response is None:
                        raise Exception("无法下载生成的图像")
                    image_content = response.content
                    
                # 列表中的元素可能是FileOutput对象
                elif hasattr(first_item, 'read'):
                    print("列表中包含FileOutput对象")
                    image_content = first_item.read()
                    
                else:
                    # 尝试转换为字符串作为URL
                    try:
                        image_url = str(first_item)
                        print(f"尝试将列表项转换为URL: {image_url}")
                        response = download_with_retry(image_url)
                        if response is None:
                            raise Exception("无法下载生成的图像")
                        image_content = response.content
                    except Exception as e:
                        raise Exception(f"无法处理列表项类型: {type(first_item)}")
                        
            # 如果是字符串（URL）
            elif isinstance(output, str):
                print(f"检测到URL字符串: {output}")
                response = download_with_retry(output)
                if response is None:
                    raise Exception("无法下载生成的图像")
                image_content = response.content
                
            else:
                # 尝试转换为字符串作为URL
                try:
                    image_url = str(output)
                    print(f"尝试转换为URL: {image_url}")
                    response = download_with_retry(image_url)
                    if response is None:
                        raise Exception("无法下载生成的图像")
                    image_content = response.content
                except Exception as e:
                    raise Exception(f"无法处理的API返回格式: {type(output)}")
            
            # 确保获得了图像内容
            if image_content is None:
                raise Exception("未能获取图像内容")
                
            # 保存图像
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_dir = os.path.join(current_dir, "generated_images")
            
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
                
            timestamp = self.logger.timestamp
            image_filename = f"{image_type}_{timestamp}.png"
            image_path = os.path.join(image_dir, image_filename)
            
            with open(image_path, "wb") as f:
                f.write(image_content)
                
            print(f"图像已保存到: {image_path}")
            
            # 保存图像路径到数据中
            self.data[save_key] = image_path
            
            # 保存图像到日志目录
            logged_path = self.logger.save_image(image_path, image_type)
            
            # 显示生成的图像
            img = Image.open(image_path)
            max_size = (320, 240)  # LCD尺寸
            img.thumbnail(max_size, Image.LANCZOS)
            self.lcd_display.show_image(img)
            
            self.logger.log_step("图像生成", f"{image_type}图像已生成并保存: {image_path}")
            
            return image_path
        except Exception as e:
            error_msg = f"生成{image_type}图像失败: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.logger.log_step("错误", error_msg)
            # 出现错误时，显示错误信息并返回None
            self.oled_display.show_text_oled(f"生成{image_type}图像失败\n请稍后再试")
            time.sleep(2)
            return None

    def handle_gen_slime_image(self):
        """处理生成史莱姆图片状态"""
        self.oled_display.show_text_oled("正在生成\n史莱姆形象...")
        
        # 生成史莱姆的图片
        slime_prompt = self.generate_image_prompt('slime')
        self.logger.log_prompt("slime_image_prompt", slime_prompt)
        
        # 使用统一的图片生成方法
        self.generate_image_with_retry(slime_prompt, 'slime_image', 'slime')

    def handle_show_slime_image(self):
        """处理显示史莱姆图片状态"""
        self.display_image_with_text(
            'slime_image',
            "史莱姆\n绘制完成！",
            "按BT1继续",
            "史莱姆图片显示成功",
            "跳过图片显示：图片未生成"
        )

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

    def _take_photo_common(self, is_new_photo=False):
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
        
        self.oled_display.show_text_oled(display_text)
        
        # 等待用户按下按钮1拍照
        self.wait_for_button(button_text)
        
        self.oled_display.show_text_oled("正在拍照...")
        
        # 运行相机脚本拍照
        run_camera_test()
        
        # 查找最新拍摄的照片
        try:
            # 先检查项目根目录是否有照片
            photo_path = os.path.join(self.get_project_root(), "current_image.jpg")
            if not os.path.exists(photo_path):
                raise FileNotFoundError("未找到拍摄的照片")
            
            # 保存带时间戳的照片副本
            timestamped_key = self.save_photo_with_timestamp(photo_path, is_new_photo)
            
            # 在LCD上显示照片
            img = Image.open(photo_path)
            self.lcd_display.show_image(img)
            
            self.logger.log_step(log_step, f"{'新' if is_new_photo else ''}照片已保存: {self.data[timestamped_key]}")
            
            # 等待用户确认照片
            self.oled_display.show_text_oled("照片已拍摄\n按BT1继续")
            self.wait_for_button("按BT1继续")
            
        except Exception as e:
            error_msg = f"处理{'新' if is_new_photo else ''}照片时出错: {str(e)}"
            self.handle_error(error_msg, "照片处理失败\n请重试")
            # 出错时递归重试
            return self._take_photo_common(is_new_photo)

    def handle_take_photo(self):
        """处理拍照状态"""
        return self._take_photo_common(is_new_photo=False)

    def handle_take_new_photo(self):
        """处理拍摄新照片状态"""
        return self._take_photo_common(is_new_photo=True)

    def handle_analyze_photo(self):
        """处理分析照片状态"""
        self.oled_display.show_text_oled("正在分析\n照片...")
        
        base64_image = encode_image(self.data['timestamped_image'])
        data_url = f"data:image/jpeg;base64,{base64_image}"
        
        # 完全使用与 openai_test.py 相同的格式
        input_content = [
            {"type": "input_text", "text": "请详细描述这张照片的内容以及给人带来的感受。"},
            {"type": "input_image", "image_url": data_url}
        ]
        
        self.data['photo_description'] = self.chat_with_continuity(input_content)
        
        self.logger.log_step("照片分析", self.data['photo_description'])
        
    def handle_suggest_destination(self):
        """处理建议目的地状态 - 优化用户体验"""
        self.oled_display.show_text_oled("正在思考\n建议...")
        
        try:
            # 尝试生成更具体的建议
            suggestion_prompt = f"""
            基于照片内容和史莱姆的执念，生成一个具体的建议，引导玩家寻找符合执念的场景。
            
            照片内容: {self.data['photo_description']}
            史莱姆执念: {self.data['slime_attributes']['obsession']}
            互动语气: {self.data['slime_attributes']['tone']}
            
            请提供:
            1. 一个简短的建议(不超过20个字)
            2. 一个简短的理由，为什么这个方向与执念相关
            
            回复格式:
            {{"suggestion": "建议", "reason": "理由"}}
            """
            
            response = self.chat_with_continuity(
                system_content="你是一个善于引导探索的史莱姆，你会根据照片内容和自己的执念，给出有针对性的建议。",
                prompt=suggestion_prompt
            )
            
            suggestion_data = self.parse_json_response(response, {"suggestion": "去寻找更多有趣的东西吧！", "reason": "可能会符合我的执念"})
            suggestion = suggestion_data.get("suggestion", "去寻找更多有趣的东西吧！")
            reason = suggestion_data.get("reason", "")
            
            # 记录建议
            self.data['destination_suggestion'] = suggestion
            self.logger.log_step("建议目的地", f"建议: {suggestion}, 理由: {reason}")
            
            # 显示建议和理由
            display_text = f"史莱姆说：\n{suggestion}"
            if reason and len(reason) < 30:  # 如果理由不太长，也一并显示
                display_text += f"\n\n{reason}"
            
            self.wait_for_button(display_text)
            
        except Exception as e:
            # 使用统一错误处理
            self.handle_error(f"生成建议时出错: {str(e)}")
            
            # 使用备用建议
            default_suggestion = "去寻找更多有趣的东西吧！"
            self.data['destination_suggestion'] = default_suggestion
            self.logger.log_step("建议目的地", f"使用默认建议: {default_suggestion}")
            self.wait_for_button(f"史莱姆说：\n{default_suggestion}")

    def handle_wait_for_new_photo(self):
        """处理等待新照片状态"""
        # 生成一个有关执念的等待提示
        waiting_prompt = self.generate_text(
            'waiting_prompt', 
            obsession=self.data['slime_attributes']['obsession'],
            tone=self.data['slime_attributes']['tone']  # 添加缺少的tone参数
        )
        
        self.logger.log_step("等待新照片", waiting_prompt)
        self.wait_for_button(f"史莱姆说：\n{waiting_prompt}\n\n按下按钮1继续拍照")

    def handle_analyze_new_photo(self):
        """处理分析新照片状态"""
        self.oled_display.show_text_oled("正在分析\n照片...")
        
        base64_image = encode_image(self.data['new_timestamped_image'])
        data_url = f"data:image/jpeg;base64,{base64_image}"
        
        # 使用与前面相同的格式来分析图片
        input_content = [
            {"type": "input_text", "text": "请详细描述这张照片的内容以及给人带来的感受，尤其是与'" + 
             self.data['slime_attributes']['obsession'] + "'相关的内容。"},
            {"type": "input_image", "image_url": data_url}
        ]
        
        self.data['new_photo_description'] = self.chat_with_continuity(input_content)
        
        self.logger.log_step("新照片分析", self.data['new_photo_description'])
        self.oled_display.show_text_oled("分析完成！")

    def handle_analyze_reward(self):
        """处理分析奖励状态"""
        self.oled_display.show_text_oled("正在分析\n奖励...")
        
        # 调用奖励分析
        reward_response = self.generate_text(
            'analyze_reward',
            personality=self.data['personality'],
            obsession=self.data['slime_attributes']['obsession'],
            quirk=self.data['slime_attributes']['quirk'],
            reflex=self.data['slime_attributes']['reflex'],
            photo_description=self.data['new_photo_description']
        )
        
        # 解析响应
        default_values = {
            "is_matched": False,
            "reward_type": "egg",
            "reward_description": "一个彩色的史莱姆蛋，有着闪烁的表面和不规则的花纹",
            "reward_text": "意外收获的史莱姆蛋"
        }
        
        self.logger.log_step("奖励JSON响应", reward_response)
        reward_data = self.parse_json_response(reward_response, default_values)
        
        # 保存奖励数据
        self.data['is_obsession_matched'] = reward_data.get('is_matched', False)
        self.data['reward_type'] = reward_data.get('reward_type', 'egg')
        self.data['reward_description'] = reward_data.get('reward_description', '')
        self.data['reward_text'] = reward_data.get('reward_text', '')
        
        # 记录本次奖励
        reward_info = {
            'cycle': self.data['cycle_count'],
            'type': self.data['reward_type'],
            'text': self.data['reward_text'],
            'is_matched': self.data['is_obsession_matched']
        }
        self.data['all_rewards'].append(reward_info)
        
        self.logger.log_step("奖励分析", f"是否匹配执念: {self.data['is_obsession_matched']}, 奖励类型: {self.data['reward_type']}")
        self.logger.log_step("奖励描述", self.data['reward_description'])
        self.logger.log_step("奖励文本", self.data['reward_text'])

    def handle_generate_reward_image(self):
        """处理生成奖励图片状态"""
        # 根据奖励类型生成不同的提示词
        if self.data['reward_type'] == 'accessory':
            prompt = f"""一个奇幻的史莱姆装饰品。{self.data['reward_description']} 
            精致细腻，色彩鲜艳，儿童绘本风格，白色背景，特写镜头。这个装饰品适合用在史莱姆身上：{self.data['slime_appearance']}"""
        else:  # egg类型
            prompt = f"""一个神秘的史莱姆蛋。{self.data['reward_description']} 
            表面有闪光和微妙的纹理，儿童绘本风格，白色背景，特写镜头。"""
        
        self.logger.log_prompt("reward_image_prompt", prompt)
        
        # 使用统一的图片生成方法
        reward_image = self.generate_image_with_retry(prompt, 'reward_image', 'reward')
        
        # 记录奖励到总列表
        reward_record = {
            'type': self.data['reward_type'],
            'description': self.data['reward_description'],
            'text': self.data['reward_text'],
            'image': reward_image
        }
        self.data['all_rewards'].append(reward_record)
        
        # 保存奖励列表到日志
        self.logger.log_step("奖励记录", f"当前获得的奖励数量: {len(self.data['all_rewards'])}")

    def handle_show_reward(self):
        """处理显示奖励状态"""
        self.display_image_with_text(
            'reward_image',
            f"奖励:\n{self.data['reward_text']}",
            "按BT1继续",
            "奖励图片显示成功",
            "跳过奖励图片显示：图片未生成"
        )

    def handle_generate_feedback(self):
        """处理生成反馈状态"""
        self.oled_display.show_text_oled("正在生成\n反馈...")
        
        # 创建反馈提示词
        if self.data['is_obsession_matched']:
            feedback_prompt = f"""
            史莱姆的执念得到了满足！请根据以下信息生成史莱姆的正面反馈：
            
            史莱姆的性格: {self.data['personality']}
            互动语气: {self.data['slime_attributes']['tone']}
            照片内容: {self.data['new_photo_description']}
            奖励物品: {self.data['reward_text']}
            
            请提供两部分内容：
            1. 反馈文本: 简短的反馈语(不超过20个字)，史莱姆应该很开心
            2. 反馈描述: 描述史莱姆开心的表情和动作(用于生成图片)
            
            请以JSON格式返回：
            {{"feedback_text": "反馈文本", "feedback_description": "反馈描述"}}
            """
        else:
            feedback_prompt = f"""
            史莱姆的执念没有得到满足，但发现了意外惊喜。请根据以下信息生成史莱姆的反馈：
            
            史莱姆的性格: {self.data['personality']}
            偏执反应: {self.data['slime_attributes']['reflex']}
            互动语气: {self.data['slime_attributes']['tone']}
            照片内容: {self.data['new_photo_description']}
            奖励物品: {self.data['reward_text']}
            
            请提供两部分内容：
            1. 反馈文本: 简短的反馈语(不超过20个字)，史莱姆应该有些意外但不失望
            2. 反馈描述: 描述史莱姆好奇或惊讶的表情和动作(用于生成图片)
            
            请以JSON格式返回：
            {{"feedback_text": "反馈文本", "feedback_description": "反馈描述"}}
            """
        
        # 生成反馈
        feedback_response = self.chat_with_continuity(
            system_content="你是一个创意角色反馈生成器。请根据角色性格生成真实、具体的反馈内容。",
            prompt=feedback_prompt
        )
        
        self.logger.log_response("feedback_response", feedback_response)
        self.logger.log_step("反馈JSON响应", feedback_response)
        
        # 解析反馈响应
        default_feedback = {
            "feedback_text": "谢谢你的努力！" if self.data['is_obsession_matched'] else "这个也不错呢~",
            "feedback_description": "史莱姆开心地跳跃，眼睛闪烁着喜悦的光芒" if self.data['is_obsession_matched'] 
                                  else "史莱姆歪着头，眼睛里充满好奇和一丝惊喜"
        }
        
        feedback_data = self.parse_json_response(feedback_response, default_feedback)
        
        # 保存反馈数据
        self.data['feedback_text'] = feedback_data.get('feedback_text', default_feedback['feedback_text'])
        self.data['feedback_description'] = feedback_data.get('feedback_description', default_feedback['feedback_description'])
        
        self.logger.log_step("反馈文本", self.data['feedback_text'])
        self.logger.log_step("反馈描述", self.data['feedback_description'])
        
        # 生成反馈图片
        feedback_prompt = f"""一个生动的史莱姆表情反应。{self.data['slime_appearance']} 
        表情生动，{self.data['feedback_description']} 儿童绘本风格，明亮的背景，色彩鲜艳。"""
        
        self.logger.log_prompt("feedback_image_prompt", feedback_prompt)
        
        # 使用统一的图片生成方法
        self.generate_image_with_retry(feedback_prompt, 'feedback_image', 'feedback')

    def handle_show_feedback(self):
        """处理显示反馈状态"""
        # 如果图片存在，使用统一显示方法；否则只显示文本
        if self.data.get('feedback_image') and os.path.exists(self.data['feedback_image']):
            self.display_image_with_text(
                'feedback_image',
                f"史莱姆说：\n{self.data['feedback_text']}",
                "按BT1继续",
                "反馈图片显示成功"
            )
        else:
            self.logger.log_step("显示反馈", "跳过反馈图片显示：图片未生成")
            self.wait_for_button(f"史莱姆说：\n{self.data['feedback_text']}\n\n按BT1继续")

    def handle_ask_continue(self):
        """处理询问是否继续状态"""
        # 生成继续询问文本
        continue_question = self.generate_text(
            'continue_question',
            personality=self.data['personality'],
            tone=self.data['slime_attributes']['tone']  # 添加tone参数
        )
        
        self.logger.log_step("询问继续", f"询问文本: {continue_question}")
        
        # 使用新的 show_continue_drift_option 方法显示选择界面
        self.data['continue_derive'] = self.oled_display.show_continue_drift_option(
            self.controller,
            question=continue_question
        )
        
        # 记录用户选择
        if self.data['continue_derive']:
            self.logger.log_step("用户选择", "继续漂流")
            self.oled_display.show_text_oled("准备继续漂流...")
        else:
            self.logger.log_step("用户选择", "结束漂流")
            self.oled_display.show_text_oled("准备结束漂流...")
        
        time.sleep(1)

    def handle_summary(self):
        """处理总结状态 - 增强版"""
        self.oled_display.show_text_oled("正在总结\n漂流经历...")
        
        try:
            # 构建漂流总结的提示词
            cycle_count = self.data['cycle_count']
            rewards_list = []
            
            for i, reward in enumerate(self.data['all_rewards']):
                match_status = "符合执念" if reward.get('is_matched', False) else "不符合执念"
                rewards_list.append(f"{reward.get('text', '奖励')} ({match_status})")
            
            rewards_text = "、".join(rewards_list) if rewards_list else "没有获得奖励"
            
            summary_prompt = f"""
            请以史莱姆的口吻，总结这次漂流经历。满足以下要求：
            
            1. 使用史莱姆的互动语气：{self.data['slime_attributes']['tone']}
            2. 提到玩家完成了{cycle_count+1}次漂流
            3. 提到获得的奖励：{rewards_text}
            4. 表达对这次漂流的感受
            5. 说一句温馨的告别
            
            总结控制在50字以内，情感要真挚，展现史莱姆的性格特点。
            """
            
            # 生成总结
            self.data['summary'] = self.chat_with_continuity(
                system_content="你是一个充满个性的史莱姆，正在与玩家告别。你的回复应当情感丰富，符合你的性格特点。",
                prompt=summary_prompt
            )
            
            self.logger.log_step("漂流总结", self.data['summary'])
            
            # 生成总结图片
            summary_image_prompt = f"""
            一个可爱的史莱姆正在告别。{self.data['slime_appearance']}
            史莱姆表情带有一丝不舍但很满足，背景有漂流中收集到的物品和记忆。
            如果有获得装饰物奖励，史莱姆应该佩戴着这些装饰。
            画面温馨感人，色彩明亮但带有一丝离别的感伤。
            儿童绘本风格，高质量插画，细节丰富。
            """
            
            # 尝试生成总结图片，不强制要求成功
            try:
                self.generate_image_with_retry(summary_image_prompt, 'summary_image', 'summary')
            except Exception:
                # 图片生成失败不影响总结流程
                self.logger.log_step("总结图片", "总结图片生成失败，将只显示文字")
            
            # 显示总结（优先显示图片，否则只显示文字）
            if self.data.get('summary_image') and os.path.exists(self.data['summary_image']):
                self.display_image_with_text(
                    'summary_image',
                    f"史莱姆说：\n{self.data['summary']}",
                    "按BT1结束漂流",
                    "总结图片显示成功"
                )
            else:
                self.wait_for_button(f"史莱姆说：\n{self.data['summary']}\n\n按BT1结束漂流")
                
            # 再见图像
            final_text = "感谢体验\n史莱姆漂流!"
            self.oled_display.show_text_oled(final_text)
            time.sleep(3)
        
        except Exception as e:
            # 使用统一的错误处理
            self.handle_error(f"生成总结时出错: {str(e)}")
            
            # 使用默认总结
            self.data['summary'] = "谢谢你陪我漂流！希望我们的旅程给你带来了快乐，下次再见！"
            self.logger.log_step("漂流总结", f"使用默认总结: {self.data['summary']}")
            self.wait_for_button(f"史莱姆说：\n{self.data['summary']}\n\n按BT1结束漂流")

    def handle_cleanup(self):
        """处理清理状态"""
        try:
            # 先保存日志
            if not self.state == DeriveState.EXIT:  # 如果不是正常退出，记录一下
                self.logger.log_step("清理", "程序结束，清理资源")
                self.logger.save_log()
            
            # 清理 GPIO
            GPIO.cleanup()
            
            # 清理其他资源
            self.controller.cleanup()
            self.lcd_display.clear()
            self.oled_display.clear()
            
        except Exception as e:
            print(f"清理过程中出错: {e}")
        return
    
    def run(self):
        """运行状态机 - 增强错误处理并添加长按返回功能"""
        state_transitions = {
            DeriveState.INIT: DeriveState.GEN_SLIME_IMAGE,
            DeriveState.GEN_SLIME_IMAGE: DeriveState.SHOW_SLIME_IMAGE,
            DeriveState.SHOW_SLIME_IMAGE: DeriveState.SHOW_GREETING,
            DeriveState.SHOW_GREETING: DeriveState.ASK_PHOTO,
            DeriveState.ASK_PHOTO: DeriveState.TAKE_PHOTO,
            DeriveState.TAKE_PHOTO: DeriveState.ANALYZE_PHOTO,
            DeriveState.ANALYZE_PHOTO: DeriveState.SUGGEST_DESTINATION,
            DeriveState.SUGGEST_DESTINATION: DeriveState.WAIT_FOR_NEW_PHOTO,
            DeriveState.WAIT_FOR_NEW_PHOTO: DeriveState.TAKE_NEW_PHOTO,
            DeriveState.TAKE_NEW_PHOTO: DeriveState.ANALYZE_NEW_PHOTO,
            DeriveState.ANALYZE_NEW_PHOTO: DeriveState.ANALYZE_REWARD,
            DeriveState.ANALYZE_REWARD: DeriveState.GENERATE_REWARD_IMAGE,
            DeriveState.GENERATE_REWARD_IMAGE: DeriveState.SHOW_REWARD,
            DeriveState.SHOW_REWARD: DeriveState.GENERATE_FEEDBACK,
            DeriveState.GENERATE_FEEDBACK: DeriveState.SHOW_FEEDBACK,
            DeriveState.SHOW_FEEDBACK: DeriveState.ASK_CONTINUE,
            DeriveState.ASK_CONTINUE: None,
            DeriveState.SUMMARY: DeriveState.CLEANUP,
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
            DeriveState.WAIT_FOR_NEW_PHOTO: self.handle_wait_for_new_photo,
            DeriveState.TAKE_NEW_PHOTO: self.handle_take_new_photo,
            DeriveState.ANALYZE_NEW_PHOTO: self.handle_analyze_new_photo,
            DeriveState.ANALYZE_REWARD: self.handle_analyze_reward,
            DeriveState.GENERATE_REWARD_IMAGE: self.handle_generate_reward_image,
            DeriveState.SHOW_REWARD: self.handle_show_reward,
            DeriveState.GENERATE_FEEDBACK: self.handle_generate_feedback,
            DeriveState.SHOW_FEEDBACK: self.handle_show_feedback,
            DeriveState.ASK_CONTINUE: self.handle_ask_continue,
            DeriveState.SUMMARY: self.handle_summary,
            DeriveState.CLEANUP: self.handle_cleanup
        }
        
        try:
            while self.state != DeriveState.EXIT:
                print(f"\n🔄 当前状态: {self.state.name}")
                
                # 检查是否长按按钮2
                if self.check_btn2_long_press():
                    print("长按检测到，终止当前流程")
                    self.state = DeriveState.CLEANUP
                    continue
                
                handler = state_handlers.get(self.state)
                
                if handler:
                    try:
                        handler()
                        
                        # 再次检查长按（确保在长时间操作后也能检测到）
                        if self.return_to_menu:
                            self.state = DeriveState.CLEANUP
                            continue
                            
                        print(f"✅ 状态 {self.state.name} 处理完成")
                        
                        # 特殊处理ASK_CONTINUE状态
                        if self.state == DeriveState.ASK_CONTINUE:
                            if self.data['continue_derive']:
                                print("👉 用户选择继续漂流")
                                self.state = DeriveState.WAIT_FOR_NEW_PHOTO
                                self.data['cycle_count'] += 1
                                print(f"📊 漂流循环次数增加至: {self.data['cycle_count']}")
                            else:
                                print("👉 用户选择结束漂流")
                                self.state = DeriveState.SUMMARY
                        else:
                            # 常规状态转换
                            next_state = state_transitions.get(self.state)
                            if next_state is not None:
                                print(f"👉 转换到状态: {next_state.name}")
                                self.state = next_state
                            else:
                                print("⚠️ 未定义下一状态，转到清理阶段")
                                self.state = DeriveState.CLEANUP
                    
                    except Exception as e:
                        error_msg = f"状态 {self.state.name} 处理出错: {str(e)}"
                        import traceback
                        traceback.print_exc()
                        self.handle_error(error_msg, step_name="状态错误")
                        self.state = DeriveState.CLEANUP
                else:
                    error_msg = f"未知状态: {self.state}"
                    self.handle_error(error_msg, step_name="状态错误")
                    self.state = DeriveState.CLEANUP
                    
        except Exception as e:
            error_msg = f"状态机运行出错: {str(e)}"
            import traceback
            traceback.print_exc()
            self.handle_error(error_msg, step_name="严重错误")
            self.logger.save_log()  # 确保在错误发生时也保存日志
        
        finally:
            # 无论如何，尝试清理并退出
            try:
                if self.state != DeriveState.EXIT:
                    print("\n🧹 开始最终清理")
                    self.handle_cleanup()
            except Exception as cleanup_error:
                print(f"\n⚠️ 清理过程中出错: {cleanup_error}")
                import traceback
                traceback.print_exc()

            # 返回菜单的标志
            return self.return_to_menu

    def extract_slime_attributes(self, personality_text):
        """从性格描述中提取史莱姆的属性 - 修改提示词格式"""
        # 尝试使用GPT提取关键属性
        prompt = f"""
        请从以下史莱姆的性格描述中提取四个关键属性。你的回复必须是严格的JSON格式，不要添加任何其他文本、标记或注释。
        
        性格描述:
        {personality_text}
        
        请仅返回以下JSON格式(不要有任何其他内容，如markdown标记、代码块等):
        {{
            "obsession": "执念内容",
            "quirk": "幻想癖好内容",
            "reflex": "偏执反应内容",
            "tone": "互动语气内容"
        }}
        """
        
        try:
            # 多次尝试提取，最多尝试3次
            for attempt in range(3):
                try:
                    response = self.chat_with_continuity(
                        system_content="你是一个数据提取助手。你的任务是准确提取文本中的关键信息，并以JSON格式返回，不添加任何其他内容，如代码块标记、注释等。",
                        prompt=prompt
                    )
                    
                    # 尝试解析JSON
                    # 清理可能的markdown标记
                    cleaned_response = response
                    if "```json" in cleaned_response:
                        cleaned_response = cleaned_response.replace("```json", "").replace("```", "")
                    
                    attributes = json.loads(cleaned_response)
                    
                    # 验证所有必需的键是否存在
                    required_keys = ['obsession', 'quirk', 'reflex', 'tone']
                    missing_keys = [key for key in required_keys if not attributes.get(key)]
                    
                    if missing_keys:
                        if attempt < 2:  # 如果还有尝试机会
                            self.logger.log_step("属性提取", f"提取不完整，缺少: {missing_keys}，尝试重新提取")
                            continue  # 重试
                    else:
                        # 所有属性都已提取
                        self.data['slime_attributes']['obsession'] = attributes.get('obsession')
                        self.data['slime_attributes']['quirk'] = attributes.get('quirk')
                        self.data['slime_attributes']['reflex'] = attributes.get('reflex')
                        self.data['slime_attributes']['tone'] = attributes.get('tone')
                        self.logger.log_step("属性提取", f"成功提取史莱姆属性: {self.data['slime_attributes']}")
                        return  # 成功提取，退出函数
                
                except json.JSONDecodeError:
                    if attempt < 2:  # 如果还有尝试机会
                        self.logger.log_step("属性提取", "JSON解析失败，尝试重新提取")
                        continue  # 重试
            
            # 如果多次尝试后仍未成功，使用文本匹配
            self.logger.log_step("属性提取", "使用文本匹配方法提取属性")
            
            # 文本匹配逻辑，查找可能的关键词和标记
            attributes = {}
            patterns = [
                ('obsession', ['执念', '执着', 'obsession']),
                ('quirk', ['幻想癖好', '癖好', '习惯', 'quirk']),
                ('reflex', ['偏执反应', '反应', 'reflex']),
                ('tone', ['互动语气', '语气', '语调', 'tone'])
            ]
            
            for attr, keywords in patterns:
                for keyword in keywords:
                    if keyword in personality_text.lower():
                        for line in personality_text.split('\n'):
                            if keyword in line.lower():
                                # 尝试提取冒号或破折号后的内容
                                if ':' in line:
                                    value = line.split(':', 1)[1].strip()
                                    attributes[attr] = value
                                    break
                                elif '：' in line:
                                    value = line.split('：', 1)[1].strip()
                                    attributes[attr] = value
                                    break
                                elif '-' in line:
                                    value = line.split('-', 1)[1].strip()
                                    attributes[attr] = value
                                    break
                
            # 将提取的属性保存到数据中
            for attr in ['obsession', 'quirk', 'reflex', 'tone']:
                if attr in attributes and attributes[attr]:
                    self.data['slime_attributes'][attr] = attributes[attr]
                else:
                    # 如果未能提取，设置默认值
                    default_values = self.get_default_slime_attributes()
                    self.data['slime_attributes'][attr] = default_values[attr]
                    self.logger.log_step("属性提取", f"未能提取{attr}，使用默认值")
            
            self.logger.log_step("属性提取", f"文本匹配提取结果: {self.data['slime_attributes']}")
                
        except Exception as e:
            # 使用统一的错误处理
            self.handle_error(f"提取属性时出错: {e}", step_name="属性提取错误")
            
            # 设置默认值确保程序可以继续
            default_attributes = self.get_default_slime_attributes()
            
            for attr, value in default_attributes.items():
                if not self.data['slime_attributes'][attr]:
                    self.data['slime_attributes'][attr] = value
            
            self.logger.log_step("属性提取", f"使用默认属性值: {self.data['slime_attributes']}")

    def parse_json_response(self, response_text, default_values=None):
        """解析JSON格式的响应 - 增强版"""
        try:
            # 尝试直接解析
            json_data = json.loads(response_text)
            return json_data
        except json.JSONDecodeError:
            # 尝试提取花括号内的内容
            try:
                # 查找第一个 { 和最后一个 }
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx+1]
                    return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass
            
            # 尝试修复常见的JSON错误并重新解析
            try:
                # 查找类似JSON结构的内容
                fixed_text = response_text.replace("'", '"')  # 将单引号替换为双引号
                
                # 处理可能的注释
                lines = fixed_text.split('\n')
                json_lines = []
                for line in lines:
                    if '//' in line:
                        line = line.split('//', 1)[0]
                    json_lines.append(line)
                
                fixed_text = '\n'.join(json_lines)
                
                # 再次查找 { }
                start_idx = fixed_text.find('{')
                end_idx = fixed_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = fixed_text[start_idx:end_idx+1]
                    return json.loads(json_str)
            except:
                pass
            
            # 如果还是无法解析，记录警告并使用默认值
            warn_msg = f"无法解析JSON响应，使用默认值: {response_text[:100]}..."
            self.logger.log_step("警告", warn_msg)
            print(f"\n⚠️ {warn_msg}")
            return default_values or {}

    def check_btn2_long_press(self):
        """检测按钮2是否被长按"""
        current_btn2 = GPIO.input(self.controller.BUTTON_PINS['BTN2'])
        current_time = time.time()
        
        # 按钮状态变化：从未按下到按下
        if current_btn2 == 0 and self.btn2_state == 1:
            self.btn2_pressed_time = current_time
            self.btn2_state = 0
        
        # 按钮状态变化：从按下到释放
        elif current_btn2 == 1 and self.btn2_state == 0:
            self.btn2_state = 1
            self.btn2_pressed_time = 0
        
        # 检查是否长按
        elif current_btn2 == 0 and self.btn2_state == 0:
            if current_time - self.btn2_pressed_time >= self.btn2_long_press_threshold:
                print("检测到按钮2长按，准备返回菜单")
                self.oled_display.show_text_oled("正在返回菜单...")
                time.sleep(0.5)
                self.return_to_menu = True
                return True
        
        return False

def main():
    # 设置信号处理
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # 获取初始文本
    initial_text = "感觉空气布满了水雾，有一种看不清前方道路的错觉，觉得很放松。你能带我在这个氛围里面漂流吗？"
    
    # 运行状态机
    state_machine = DeriveStateMachine(initial_text)
    return_to_menu = state_machine.run()
    
    # 如果需要返回菜单，退出码设为特殊值
    if return_to_menu:
        print("正常返回菜单系统")
        sys.exit(42)  # 使用特殊退出码表示返回菜单
    else:
        print("正常结束程序")
        sys.exit(0)

if __name__ == "__main__":
    main() 