import subprocess
import os
import sys
import base64
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 拍照函数
def run_camera_test():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    camera_script = os.path.join(current_dir, "camera_test.py")

    try:
        print("启动拍照脚本...")
        subprocess.run(["/usr/bin/python3", camera_script], check=True)  # 或sys.executable
        print("拍照完成。")
    except subprocess.CalledProcessError as e:
        print(f"拍照脚本运行出错: {e}")

# 编码图片成base64
def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# 主流程
def main():
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

    # 第3步：生成史莱姆描述的 prompt
    slime_prompt = f"绘制一只史莱姆，主题灵感来自：'{description}'。请用游戏风格，颜色清新，表情可爱。"

    print("\n🎨 生成史莱姆提示词：", slime_prompt)

    # 第4步：用gpt-image-1生成史莱姆图片
    print("\n🖌️ 开始绘制史莱姆图片...")
    result = client.images.generate(
        model="gpt-image-1",
        prompt=slime_prompt
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    # 第5步：保存新生成的史莱姆图片
    output_path = os.path.join(current_dir, "new_slime.png")
    with open(output_path, "wb") as f:
        f.write(image_bytes)

    print(f"\n✅ 新史莱姆绘制完成，已保存为: {output_path}")

if __name__ == "__main__":
    main()