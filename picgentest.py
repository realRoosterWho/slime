import os
import replicate
from PIL import Image
import requests
from io import BytesIO
from dotenv import load_dotenv

def test_image_generation():
    # 加载环境变量
    load_dotenv()
    
    # 获取并检查 API token
    replicate_api_key = os.getenv("REPLICATE_API_KEY")
    if not replicate_api_key:
        raise Exception("没有找到 REPLICATE_API_KEY")
    
    print(f"API Key 前几位: {replicate_api_key[:8]}...")
    
    # 创建客户端并设置 token
    os.environ["REPLICATE_API_TOKEN"] = replicate_api_key
    
    # 测试参数
    prompt = "a cute slime creature with big eyes, children's book style, colorful and adorable"
    
    try:
        print("开始生成图片...")
        print(f"使用提示词: {prompt}")
        
        output = replicate.run(
            "black-forest-labs/flux-1.1-pro",
            input={
                "prompt": prompt,
                "prompt_upsampling": True,
                "width": 512,
                "height": 512,
                "num_outputs": 1,
                "scheduler": "K_EULER",
                "num_inference_steps": 25,
                "guidance_scale": 7.5,
            }
        )
        
        print(f"API 返回: {output}")
        
        if output and isinstance(output, list):
            # 下载图片
            response = requests.get(output[0])
            if response.status_code == 200:
                # 保存原始图片
                img = Image.open(BytesIO(response.content))
                img.save("test_original.png")
                print("原始图片已保存为 test_original.png")
                
                # 调整大小并保存
                resized = img.resize((320, 240), Image.Resampling.LANCZOS)
                resized.save("test_resized.png")
                print("调整大小后的图片已保存为 test_resized.png")
            else:
                print(f"下载图片失败，状态码: {response.status_code}")
        else:
            print("API 返回格式错误")
            
    except Exception as e:
        print(f"发生错误: {type(e).__name__}")
        print(f"错误信息: {str(e)}")

if __name__ == "__main__":
    test_image_generation() 