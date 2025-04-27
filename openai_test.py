import os
import base64
from openai import OpenAI
from dotenv import load_dotenv
import cameraManager  # 你自己写的那个，注意名字对上

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 第一步：调用cameraManager，拍照
cameraManager.run_camera_test()

# 第二步：读取拍好的图片
image_path = os.path.join(os.path.dirname(__file__), "current_image.jpg")

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

base64_image = encode_image(image_path)
data_url = f"data:image/jpeg;base64,{base64_image}"

# 第三步：发送给 OpenAI
response = client.responses.create(
    model="gpt-4o",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "请描述这张照片的内容。"},
                {"type": "input_image", "image_url": data_url}
            ]
        }
    ]
)

# 第四步：打印OpenAI返回的描述
print("\n📷 OpenAI返回的图片描述：")
print(response.output[0].content[0].text)