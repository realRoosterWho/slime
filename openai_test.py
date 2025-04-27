import base64
from openai import OpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 编码图片为 base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# 你的本地图片路径
image_path = "slime1.png"  # 换成你的图路径
base64_image = encode_image(image_path)

# 用 responses.create 发送图像+文本
response = client.responses.create(
    model="gpt-4o",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "请描述这张图片。"},
                {
                    "type": "input_image",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    ]
)

# 打印输出
print(response.output[0].content[0].text)