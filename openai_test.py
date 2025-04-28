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

# 加载环境变量
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
replicate_api_key = os.getenv("REPLICATE_API_KEY")

if not replicate_api_key:
    raise Exception("没有找到REPLICATE_API_KEY，请检查.env文件设置！")

replicate_client = replicate.Client(api_token=replicate_api_key)

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
    response = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "请简短描述这张照片的主要内容。"},
                    {"type": "input_image", "image_url": data_url}
                ]
            }
        ]
    )

    description = response.output[0].content[0].text.strip()
    print("\n📷 识别结果：", description)

    # 第3步：生成史莱姆性格描述
    slime_personality = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一个专业的角色设定师。根据环境或物体的描述，帮我设定一只史莱姆的小档案，包括它的性格、表情、动作特点等，用英文简洁描述，不要太长，情感要细腻。"},
            {"role": "user", "content": f"根据这个描述设定一只史莱姆：{description}"}
        ]
    )

    slime_personality_text = slime_personality.choices[0].message.content.strip()

    # 新增：生成打招呼文本
    greeting = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一个可爱的史莱姆。请根据给定的性格描述，生成一句简短的打招呼用语，要可爱活泼，不超过20个字。"},
            {"role": "user", "content": f"根据这个性格描述生成打招呼用语：{slime_personality_text}"}
        ]
    )

    greeting_text = greeting.choices[0].message.content.strip()
    print("\n👋 史莱姆打招呼：", greeting_text)

    # 在OLED上显示打招呼文本
    oled_display.show_text_oled(greeting_text)
    time.sleep(3)  # 显示3秒

    # 继续生成史莱姆图片的prompt
    slime_prompt = f"A fantasy slime creature. {slime_personality_text} Children's book illustration style, colorful and cute. Slime is a cute and fluffy creature, has two big eyes and a small mouth."

    print("\n🎨 生成史莱姆提示词：", slime_prompt)

    # 第4步：用Replicate的 Flux-1.1-Pro 生成史莱姆图片
    # print("\n🖌️ 开始绘制史莱姆图片（Replicate生成）...")
    # output = replicate_client.run(
    #     "black-forest-labs/flux-1.1-pro",
    #     input={
    #         "prompt": slime_prompt,
    #         "prompt_upsampling": True
    #     }
    # )

    # # output 是文件流，直接保存
    # output_path = os.path.join(current_dir, "new_slime.png")
    # with open(output_path, "wb") as f:
    #     f.write(output.read())

    # print(f"\n✅ 新史莱姆绘制完成，已保存为: {output_path}")

    # 第五步：在LCD上显示图片
    try:
        print("\n📺 正在显示史莱姆图片...")
        lcd_display.show_image(output_path)
        time.sleep(60)  # 显示5秒
        lcd_display.clear()  # 清除显示
    except Exception as e:
        print(f"显示图片时出错: {e}")

if __name__ == "__main__":
    main()