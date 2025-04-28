import os
import replicate
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY")

if not REPLICATE_API_KEY:
    raise Exception("没有找到REPLICATE_API_KEY，请检查.env文件设置！")

client = replicate.Client(api_token=REPLICATE_API_KEY)

# Prompt
prompt = """
A melancholic slime creature sitting alone under a gray, rainy sky.
The slime looks translucent and slightly glowing, with sad, drooping eyes.
The environment is misty and blurred, evoking a deep sense of loneliness and quiet sorrow.
Children's book illustration style, soft watercolor texture, highly detailed, fantasy setting.
"""

print("正在生成图片，请稍等...")

output = client.run(
    "black-forest-labs/flux-1.1-pro",
    input={
        "prompt": prompt,
        "prompt_upsampling": True
    }
)

# 直接用 .path
image_url = output.path
print(f"图片生成成功！图片地址: {image_url}")

# 下载图片保存
image_response = requests.get(image_url)
if image_response.status_code == 200:
    with open("melancholic_slime.png", "wb") as f:
        f.write(image_response.content)
    print("✅ 图片已保存为 melancholic_slime.png")
else:
    print(f"下载图片失败，状态码: {image_response.status_code}")