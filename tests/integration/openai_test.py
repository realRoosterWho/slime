import subprocess
import os
import sys
import base64
import replicate
import requests
import time
from openai import OpenAI
from dotenv import load_dotenv
from display_utils import DisplayManager
from stt_utils import SpeechToText
import signal

# 加载环境变量
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
replicate_api_key = os.getenv("REPLICATE_API_KEY")

if not replicate_api_key:
    raise Exception("没有找到REPLICATE_API_KEY，请检查.env文件设置！")

replicate_client = replicate.Client(api_token=replicate_api_key)

def chat_with_gpt(input_content, system_content=None, previous_response_id=None):
    """
    与GPT进行对话
    
    Args:
        input_content: 用户输入内容
        system_content: 系统提示词
        previous_response_id: 上一轮对话的ID
        
    Returns:
        response: 对话响应对象
    """
    input_data = [{"role": "user", "content": input_content}]
    if system_content:
        input_data.insert(0, {"role": "system", "content": system_content})
        
    response = client.responses.create(
        model="gpt-4o",
        input=input_data,
        previous_response_id=None
    )
    return response

# 拍照函数
def run_camera_test():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    camera_script = os.path.join(current_dir, "camera_test.py")

    try:
        print("启动拍照脚本...")
        subprocess.run(["/usr/bin/python3", camera_script], check=True)
        print("拍照完成。")
    except subprocess.CalledProcessError as e:
        print(f"拍照脚本运行出错: {e}")

# 编码图片成base64
def encode_image(image_path):
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

# 主流程
def main():
    # 设置信号处理
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # 初始化显示管理器
    print("初始化显示设备...")
    print("正在初始化OLED...")
    oled_display = DisplayManager("OLED")
    oled_display.show_text_oled("初始化中...")
    
    print("正在初始化LCD (BitBang模式)...")
    lcd_display = DisplayManager("LCD")
    oled_display.show_text_oled("初始化完成")
    time.sleep(1)

    # 第1步：拍照
    oled_display.show_text_oled("准备拍照...")
    run_camera_test()
    oled_display.show_text_oled("拍照完成")
    time.sleep(1)

    # 第2步：读取图片，做识别
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "current_image.jpg")
    oled_display.show_text_oled("正在分析\n图片...")
    
    base64_image = encode_image(image_path)
    data_url = f"data:image/jpeg;base64,{base64_image}"

    print("发送照片识别请求...")
    # 第一轮：图片识别
    response = chat_with_gpt(
        input_content=[
            {"type": "input_text", "text": "请简短描述这张照片的主要内容。"},
            {"type": "input_image", "image_url": data_url}
        ]
    )
    description = response.output[0].content[0].text.strip()
    print("\n📷 识别结果：", description)
    oled_display.show_text_oled("识别完成")
    time.sleep(1)

    # 第二轮：生成史莱姆性格
    oled_display.show_text_oled("正在生成\n史莱姆性格...")
    response = chat_with_gpt(
        system_content="你是一个专业的角色设定师。根据环境或物体的描述，帮我设定一只史莱姆的小档案，包括它的性格、表情、动作特点等，用英文简洁描述，不要太长，情感要细腻。",
        input_content=f"根据这个描述设定一只史莱姆：{description}",
        previous_response_id=response.id
    )
    slime_personality_text = response.output[0].content[0].text.strip()
    oled_display.show_text_oled("性格设定完成")
    time.sleep(1)

    # 第三轮：生成打招呼
    oled_display.show_text_oled("正在想打招呼\n的话...")
    response = chat_with_gpt(
        system_content="你是一个可爱的史莱姆。请根据给定的性格描述说话，中文，不超过15个字。",
        input_content=f"根据这个性格描述生成打招呼用语：{slime_personality_text}",
        previous_response_id=response.id
    )
    greeting_text = response.output[0].content[0].text.strip()
    print("\n👋 史莱姆打招呼：", greeting_text)

    # 在OLED上显示打招呼文本
    oled_display.show_text_oled(greeting_text)
    time.sleep(3)

    # 生成史莱姆图片
    oled_display.show_text_oled("正在绘制\n史莱姆...")
    slime_prompt = f"""
    Create a charming pixel art slime character. {slime_personality_text}
    
    Design the slime as a simple blob shape with large eyes and a tiny mouth, showing its unique personality traits.
    
    Render in Game Boy style monochrome pixel art using only black and white pixels.
    """
    print("\n🎨 生成史莱姆提示词：", slime_prompt)

    # 第4步：用Replicate生成史莱姆图片
    print("\n🖌️ 开始绘制史莱姆图片（Replicate生成）...")
    output = replicate_client.run(
        "black-forest-labs/flux-schnell",
        input={
            "prompt": slime_prompt,
            "prompt_upsampling": True,
            "width": 320,        # 匹配LCD宽度
            "height": 240,       # 匹配LCD高度
            "num_inference_steps": 4  # flux-schnell模型最大支持4步
        }
    )

    # 从返回的URL下载图片
    if isinstance(output, list) and len(output) > 0:
        image_url = output[0]
        print(f"正在下载图片: {image_url}")
        oled_display.show_text_oled("正在下载\n史莱姆图片...")
        
        try:
            img_response = download_with_retry(image_url)
            if img_response:
                output_path = os.path.join(current_dir, "new_slime.png")
                with open(output_path, "wb") as f:
                    f.write(img_response.content)
                print(f"\n✅ 新史莱姆绘制完成，已保存为: {output_path}")
                oled_display.show_text_oled("史莱姆\n绘制完成！")
                time.sleep(1)
            else:
                print("下载图片失败")
                oled_display.show_text_oled("图片下载失败")
        except Exception as e:
            print(f"下载图片时出错: {e}")
            oled_display.show_text_oled("图片下载失败")
    else:
        print("生成图片失败，没有获取到有效的URL")
        oled_display.show_text_oled("图片生成失败")

    # 第五步：在LCD上显示图片并处理语音输入
    try:
        print("\n📺 正在显示史莱姆图片...")
        lcd_display.show_image(output_path)
        
        # 显示语音输入提示
        print("\n🎤 准备录音...")
        oled_display.show_text_oled("请说话...\n(5秒)")
        time.sleep(1)  # 给用户一点准备时间
        
        # 语音输入
        stt = SpeechToText()
        user_input = stt.record_and_transcribe(duration=5)
        print(f"\n👂 你说的是: {user_input}")
        
        # 显示识别结果
        oled_display.show_text_oled(f"识别结果:\n{user_input}")
        time.sleep(3)  # 显示3秒识别结果
        
        # 显示思考提示
        oled_display.show_text_oled("思考中...")
        
        # 第四轮：生成史莱姆的回答
        response = chat_with_gpt(
            system_content="你是一个可爱的史莱姆。请根据给定的性格描述说话，不超过15个字。",
            input_content=f"性格描述：{slime_personality_text}\n用户说：{user_input}，请你根据这个给回答，并给他一个漂流的提示（下一步去向哪里）",
            previous_response_id=response.id
        )
        
        response_text = response.output[0].content[0].text.strip()
        print(f"\n👋 史莱姆回答：{response_text}")
        
        # 显示史莱姆的回答
        oled_display.show_text_oled(response_text)
        time.sleep(3)
        
        time.sleep(60)
        lcd_display.clear()
    except Exception as e:
        print(f"显示图片时出错: {e}")

if __name__ == "__main__":
    main()