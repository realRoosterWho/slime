import os
import replicate
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 读取你的API Key
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY")

if not REPLICATE_API_KEY:
    raise Exception("没有找到REPLICATE_API_KEY，请检查.env文件设置！")

# 初始化Replicate客户端
client = replicate.Client(api_token=REPLICATE_API_KEY)

# 设定Prompt
prompt = "a colorful cute slime creature, children's book illustration style, highly detailed, fantasy setting"

# 调用 Replicate 的 SDXL模型生成图片
print("正在生成图片，请稍等...")
output = client.run(
    "stability-ai/sdxl:8b7e660199bab4229f59cf7c9bb39c1b880ed6f22ec8642c44240648b2b46205",
    input={
        "prompt": prompt,
        "width": 1024,
        "height": 1024
    }
)

# 输出是图片URL
image_url = output[0]
print(f"图片生成成功！图片地址: {image_url}")

# 下载图片并保存
image_response = requests.get(image_url)

if image_response.status_code == 200:
    with open("generated_slime.png", "wb") as f:
        f.write(image_response.content)
    print("✅ 图片已保存为 generated_slime.png")
else:
    print(f"下载图片失败，状态码: {image_response.status_code}")