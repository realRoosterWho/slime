from openai import OpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 第一步：上传本地图片到 OpenAI
with open("slime1.png", "rb") as f:
    uploaded_file = client.files.create(
        file=f,
        purpose="vision"  # 注意：purpose必须是vision
    )

file_id = uploaded_file.id
print(f"上传成功，file_id: {file_id}")

# 第二步：用 file_id 发请求
response = client.responses.create(
    model="gpt-4o",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "请描述这张图片。"},
                {"type": "input_image", "image_file": {"file_id": file_id}}
            ]
        }
    ]
)

# 打印模型返回内容
print(response.output[0].content[0].text)