from openai import OpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 打开本地图片
with open("slime1.png", "rb") as image_file:
    response = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "请描述这张图片。"},
                    {"type": "input_image", "image": image_file}
                ]
            }
        ]
    )

# 打印返回内容
print(response.output[0].content[0].text)