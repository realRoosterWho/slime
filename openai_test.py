import requests
import base64
from openai import OpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 上传本地图片到 sm.ms
def upload_image(image_path):
    upload_url = "https://sm.ms/api/v2/upload"
    with open(image_path, "rb") as f:
        files = {"smfile": f}
        response = requests.post(upload_url, files=files)
        result = response.json()
        if result.get("success"):
            return result["data"]["url"]
        else:
            raise Exception(f"图片上传失败: {result}")

# 上传本地 slime1.png
image_path = "slime1.png"
image_url = upload_image(image_path)

print(f"上传成功，图片URL：{image_url}")

# 用上传后的URL，发给OpenAI识别
response = client.responses.create(
    model="gpt-4o",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "请描述这张图片。"},
                {"type": "input_image", "image_url": image_url}
            ]
        }
    ]
)

# 打印OpenAI返回的描述
print(response.output[0].content[0].text)