from display_utils import DisplayManager
import time

def test_oled_text_wrapping():
    oled = DisplayManager("OLED")
    
    # 测试用例1：短文本
    print("测试1：短文本")
    oled.show_text_oled("你好世界")
    time.sleep(3)
    
    # 测试用例2：长文本，自动换行
    print("测试2：长文本自动换行")
    oled.show_text_oled("这是一段很长的文本需要自动换行显示在OLED上", chars_per_line=10)
    time.sleep(3)
    
    # 测试用例3：手动换行文本
    print("测试3：手动换行文本")
    oled.show_text_oled("第一行\n第二行\n第三行")
    time.sleep(3)
    
    # 测试用例4：不同字体大小
    print("测试4：较大字体")
    oled.show_text_oled("大字体测试", font_size=20, chars_per_line=6)
    time.sleep(3)
    
    # 测试用例5：混合中英文
    print("测试5：混合中英文")
    oled.show_text_oled("Hello你好World世界", chars_per_line=10)
    time.sleep(3)
    
    # 测试用例6：超长文本
    print("测试6：超长文本测试")
    oled.show_text_oled("这是一个超长的文本测试用例，我们要看看它是否能正确换行并且完整显示所有内容而不会截断", chars_per_line=12)
    time.sleep(3)

def debug_font_info():
    """调试字体信息"""
    oled = DisplayManager("OLED")
    test_text = "测试文本ABC123"
    
    try:
        from PIL import ImageFont
        font = ImageFont.truetype(oled.font_path, 12)
        
        # 打印字体信息
        print("\n字体调试信息：")
        print(f"字体路径: {oled.font_path}")
        print(f"测试文本: {test_text}")
        
        # 获取文本尺寸
        text_bbox = font.getbbox(test_text)
        if text_bbox:
            print(f"文本边界框: {text_bbox}")
            print(f"文本宽度: {text_bbox[2] - text_bbox[0]}")
            print(f"文本高度: {text_bbox[3] - text_bbox[1]}")
        
        # 测试单个字符
        for char in test_text:
            char_bbox = font.getbbox(char)
            if char_bbox:
                print(f"字符 '{char}' 宽度: {char_bbox[2] - char_bbox[0]}")
    
    except Exception as e:
        print(f"字体调试出错: {e}")

if __name__ == "__main__":
    print("开始OLED文本换行测试...")
    
    # 先运行字体调试
    debug_font_info()
    
    # 然后运行显示测试
    try:
        test_oled_text_wrapping()
        print("测试完成！")
    except Exception as e:
        print(f"测试过程中出错: {e}") 