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

# 主流程
def main():
    # 初始化显示管理器
    oled_display = DisplayManager("OLED")
    lcd_display = DisplayManager("LCD")

    # 第1步：拍照
    run_camera_test()

    # 第2步：读取图片，做识别
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "current_image.jpg")
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

    # 第二轮：生成史莱姆性格
    response = chat_with_gpt(
        system_content="你是一个专业的角色设定师。根据环境或物体的描述，帮我设定一只史莱姆的小档案，包括它的性格、表情、动作特点等，用英文简洁描述，不要太长，情感要细腻。",
        input_content=f"根据这个描述设定一只史莱姆：{description}",
        previous_response_id=response.id
    )
    slime_personality_text = response.output[0].content[0].text.strip()

    # 第三轮：生成打招呼
    response = chat_with_gpt(
        system_content="你是一个可爱的史莱姆。请根据给定的性格描述说话，不超过15个字。",
        input_content=f"根据这个性格描述生成打招呼用语：{slime_personality_text}",
        previous_response_id=response.id
    )
    greeting_text = response.output[0].content[0].text.strip()
    print("\n👋 史莱姆打招呼：", greeting_text)

    # 在OLED上显示打招呼文本
    oled_display.show_text_oled(greeting_text)
    time.sleep(3)

    # 生成史莱姆图片的prompt
    slime_prompt = f"A fantasy slime creature. {slime_personality_text} Children's book illustration style, colorful and cute. Slime is a cute and fluffy creature, has two big eyes and a small mouth."
    print("\n🎨 生成史莱姆提示词：", slime_prompt)

    # 第4步：用Replicate生成史莱姆图片
    print("\n🖌️ 开始绘制史莱姆图片（Replicate生成）...")
    output = replicate_client.run(
        # "black-forest-labs/flux-1.1-pro",
        "black-forest-labs/flux-schnell",
        input={
            "prompt": slime_prompt,
            "prompt_upsampling": True
        }
    )

    # 从返回的URL下载图片
    if isinstance(output, list) and len(output) > 0:
        image_url = output[0]
        print(f"正在下载图片: {image_url}")
        
        response = requests.get(image_url)
        if response.status_code == 200:
            output_path = os.path.join(current_dir, "new_slime.png")
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"\n✅ 新史莱姆绘制完成，已保存为: {output_path}")
        else:
            print(f"下载图片失败，状态码: {response.status_code}")
    else:
        print("生成图片失败，没有获取到有效的URL")

    # 第五步：在LCD上显示图片并处理语音输入
    try:
        print("\n📺 正在显示史莱姆图片...")
        lcd_display.show_image(output_path)
        
        # 添加语音输入部分
        print("\n🎤 请在15秒内说出你想对史莱姆说的话...")
        stt = SpeechToText()
        user_input = stt.record_and_transcribe(duration=15)
        print(f"\n👂 你说的是: {user_input}")
        
        # 第四轮：生成史莱姆的回答
        response = chat_with_gpt(
            system_content="你是一个可爱的史莱姆。请根据给定的性格描述说话，不超过15个字。",
            input_content=f"性格描述：{slime_personality_text}\n用户说：{user_input}，请你根据这个给回答，并给他一个漂流的提示（下一步去向哪里）",
            previous_response_id=response.id
        )
        
        response_text = response.output[0].content[0].text.strip()
        print(f"\n👋 史莱姆回答：{response_text}")
        
        # 在OLED上显示回答
        oled_display.show_text_oled(response_text)
        time.sleep(3)
        
        time.sleep(60)
        lcd_display.clear()
    except Exception as e:
        print(f"显示图片时出错: {e}")

if __name__ == "__main__":
    main()