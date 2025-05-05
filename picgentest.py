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
        
        print(f"API 返回类型: {type(output)}")
        print(f"API 返回内容: {output}")
        print(f"API 返回内容的详细信息:")
        print(f"- dir(output): {dir(output)}")
        if hasattr(output, '__dict__'):
            print(f"- output.__dict__: {output.__dict__}")
        
        # 如果返回是列表，获取第一个元素
        if isinstance(output, list):
            image_url = output[0]
            print(f"从列表中获取第一个URL: {image_url}")
        # 如果返回是字符串（URL），直接使用
        elif isinstance(output, str):
            image_url = output
            print(f"直接获取URL: {image_url}")
        else:
            # 尝试转换为字符串
            try:
                image_url = str(output)
                print(f"转换为字符串后的URL: {image_url}")
            except:
                raise Exception(f"无法处理的API返回格式: {type(output)}")
            
        # 下载图片
        print("开始下载图片...")
        response = requests.get(image_url)
        print(f"下载状态码: {response.status_code}")
        
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
            
    except Exception as e:
        print(f"发生错误: {type(e).__name__}")
        print(f"错误信息: {str(e)}")

if __name__ == "__main__":
    test_image_generation() 