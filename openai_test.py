import base64
from openai import OpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 编码图片成base64
def encode_image(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return encoded

# 你的本地图片
image_path = "slime1.png"
base64_image = encode_image(image_path)

# 构造 data:image/png;base64,xxxx 的字符串
data_url = f"data:image/png;base64,{base64_image}"

# 发送请求
response = client.responses.create(
    model="gpt-4o",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "请描述这张图片。"},
                {"type": "input_image", "image_url": data_url}
            ]
        }
    ]
)

# 打印返回结果
print(response.output[0].content[0].text)