import os
import replicate
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

# 调用Flux生成图
output = client.run(
    "black-forest-labs/flux-1.1-pro",
    input={
        "prompt": prompt,
        "prompt_upsampling": True
    }
)

# 保存到sad_slime.png
with open("sad_slime.png", "wb") as file:
    file.write(output.read())

print("✅ 图片已保存为 sad_slime.png")