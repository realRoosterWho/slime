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

def chat_with_gpt(input_content, system_content=None, previous_response_id=None):
    """与GPT进行对话"""
    input_data = [{"role": "user", "content": input_content}]
    if system_content:
        input_data.insert(0, {"role": "system", "content": system_content})
        
    response = client.responses.create(
        model="gpt-4",
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

def main():
    # 初始化日志记录器
    logger = DeriveLogger()
    logger.log_step("初始化", "开始新的漂流...")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # 初始化显示管理器
    logger.log_step("初始化显示", "初始化显示设备...")
    print("正在初始化OLED...")
    oled_display = DisplayManager("OLED")
    oled_display.show_text_oled("初始化中...")
    
    print("正在初始化LCD (BitBang模式)...")
    lcd_display = DisplayManager("LCD")
    oled_display.show_text_oled("初始化完成")
    time.sleep(1)

    try:
        # 第1步：拍照
        logger.log_step("拍照", "准备拍照...")
        oled_display.show_text_oled("准备拍照...")
        run_camera_test()
        
        # 保存原始照片
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "current_image.jpg")
        logger.save_image(image_path, "original")
        
        oled_display.show_text_oled("拍照完成")
        time.sleep(1)

        # 第2步：读取图片，做识别
        logger.log_step("图片识别", "开始分析图片...")
        oled_display.show_text_oled("正在分析\n图片...")
        
        base64_image = encode_image(image_path)
        data_url = f"data:image/jpeg;base64,{base64_image}"

        # 第一轮：图片识别
        response = chat_with_gpt(
            input_content=[
                {"type": "input_text", "text": "请简短描述这张照片的主要内容。"},
                {"type": "input_image", "image_url": data_url}
            ]
        )
        description = response.output[0].content[0].text.strip()
        logger.log_response("image_description", description)
        logger.log_step("识别结果", f"识别结果：{description}")
        
        oled_display.show_text_oled("识别完成")
        time.sleep(1)

        # 第二轮：生成史莱姆性格
        logger.log_step("生成性格", "开始生成史莱姆性格...")
        oled_display.show_text_oled("正在生成\n史莱姆性格...")
        
        personality_prompt = f"根据这个描述设定一只史莱姆：{description}"
        logger.log_prompt("personality", personality_prompt)
        
        response = chat_with_gpt(
            system_content="你是一个专业的角色设定师。根据环境或物体的描述，帮我设定一只史莱姆的小档案，包括它的性格、表情、动作特点等，用英文简洁描述，不要太长，情感要细腻。",
            input_content=personality_prompt,
            previous_response_id=response.id
        )
        slime_personality_text = response.output[0].content[0].text.strip()
        logger.log_response("personality", slime_personality_text)
        
        oled_display.show_text_oled("性格设定完成")
        time.sleep(1)

        # 第三轮：生成打招呼
        logger.log_step("生成对话", "生成打招呼语句...")
        oled_display.show_text_oled("正在想打招呼\n的话...")
        
        greeting_prompt = f"根据这个性格描述生成打招呼用语：{slime_personality_text}"
        logger.log_prompt("greeting", greeting_prompt)
        
        response = chat_with_gpt(
            system_content="你是一个可爱的史莱姆。请根据给定的性格描述说话，中文，不超过15个字。",
            input_content=greeting_prompt,
            previous_response_id=response.id
        )
        greeting_text = response.output[0].content[0].text.strip()
        logger.log_response("greeting", greeting_text)
        logger.log_step("打招呼", f"史莱姆说：{greeting_text}")

        # 在OLED上显示打招呼文本
        oled_display.show_text_oled(greeting_text)
        time.sleep(3)

        # 生成史莱姆图片
        logger.log_step("生成图片", "开始生成史莱姆图片...")
        oled_display.show_text_oled("正在绘制\n史莱姆...")
        
        slime_prompt = f"一个奇幻的史莱姆生物。{slime_personality_text} 儿童绘本插画风格，色彩丰富且可爱。史莱姆是一个可爱蓬松的生物，有两只大眼睛和一个小嘴巴。"
        logger.log_prompt("image", slime_prompt)

        # 第4步：用Replicate生成史莱姆图片
        output = replicate_client.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": slime_prompt,
                "prompt_upsampling": True,
                "width": 320,
                "height": 240,
                "num_inference_steps": 4
            }
        )

        # 从返回的URL下载图片
        if isinstance(output, list) and len(output) > 0:
            image_url = output[0]
            logger.log_step("下载图片", f"从URL下载图片: {image_url}")
            
            try:
                img_response = download_with_retry(image_url)
                if img_response:
                    output_path = os.path.join(current_dir, "new_slime.png")
                    with open(output_path, "wb") as f:
                        f.write(img_response.content)
                    
                    # 保存生成的图片
                    logger.save_image(output_path, "generated")
                    logger.log_step("图片生成", "史莱姆图片生成完成")
                    
                    oled_display.show_text_oled("史莱姆\n绘制完成！")
                    time.sleep(1)
                    
                    # 显示图片
                    lcd_display.show_image(output_path)
                    time.sleep(60)
                    lcd_display.clear()
                else:
                    logger.log_step("错误", "下载图片失败")
                    oled_display.show_text_oled("图片下载失败")
            except Exception as e:
                logger.log_step("错误", f"下载图片时出错: {str(e)}")
                oled_display.show_text_oled("图片下载失败")
        else:
            logger.log_step("错误", "生成图片失败，没有获取到有效的URL")
            oled_display.show_text_oled("图片生成失败")
    
    except Exception as e:
        logger.log_step("错误", f"程序运行出错: {str(e)}")
    
    finally:
        # 保存日志
        logger.save_log()
        
        # 清理显示
        if 'lcd_display' in locals():
            lcd_display.clear()
        if 'oled_display' in locals():
            oled_display.clear()

if __name__ == "__main__":
    main() 