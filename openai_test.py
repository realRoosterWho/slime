from openai import OpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 第一步：上传本地图片
file = client.files.create(
    file=open("slime1.png", "rb"),
    purpose="vision"  # 注意这里必须是 vision
)

# 拿到上传后的 file_id
file_id = file.id

# 第二步：用 file_id 作为 input_image
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

# 打印输出
print(response.output[0].content[0].text)