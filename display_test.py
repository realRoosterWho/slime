from display_utils import DisplayManager
import time
from input_controller import InputController

def test_lcd():
    print("测试LCD显示屏...")
    display = DisplayManager("LCD")
    
    # 测试清屏
    print("1. 测试清屏")
    display.clear()
    time.sleep(2)
    
    # 测试显示单行中文
    print("2. 测试显示单行中文")
    display.show_text("欢迎使用 Slime!", font_size=30)
    time.sleep(3)
    
    # 测试显示多行中文（手动换行）
    print("3. 测试多行中文显示")
    display.show_text("第一行测试\n第二行测试\n第三行测试", font_size=24)
    time.sleep(3)
    
    # 测试长文本自动换行
    print("4. 测试长文本自动换行")
    long_text = "这是一段较长的中文文本，用于测试显示屏的自动换行功能。系统会自动计算文本宽度并进行换行处理。"
    display.show_text(long_text, font_size=24, max_width=220)
    time.sleep(3)
    
    # 测试显示图片
    print("5. 测试显示图片")
    try:
        display.show_image("slime1.png")
        time.sleep(3)
    except:
        print("未找到图片文件，跳过图片测试")
    
    # 测试进度条
    print("6. 测试进度条")
    for i in range(11):
        display.draw_progress_bar(i/10)
        time.sleep(1)
    
    # 测试中文菜单
    print("7. 测试中文菜单")
    menu_items = ["开始游戏", "系统设置", "关于我们", "退出系统"]
    for i in range(len(menu_items)):
        display.draw_menu(menu_items, i)
        time.sleep(2)
    
    display.clear()

def test_oled():
    print("测试OLED显示屏...")
    display = DisplayManager("OLED")
    
    # 测试清屏
    print("1. 测试清屏")
    display.clear()
    time.sleep(2)
    
    # 测试显示单行中文
    print("2. 测试显示单行中文")
    display.show_text("欢迎使用!", font_size=12)
    time.sleep(3)
    
    # 测试显示多行中文
    print("3. 测试多行中文显示")
    display.show_text("第一行\n第二行\n第三行", font_size=12)
    time.sleep(3)
    
    # 测试长文本自动换行
    print("4. 测试长文本自动换行")
    long_text = "这是OLED显示测试文本，测试自动换行功能。"
    display.show_text(long_text, font_size=12, max_width=120)
    time.sleep(3)
    
    # 测试进度条
    print("5. 测试进度条")
    for i in range(11):
        display.draw_progress_bar(i/10)
        time.sleep(1)
    
    # 测试中文菜单
    print("6. 测试中文菜单")
    menu_items = ["设置", "信息", "返回"]
    for i in range(len(menu_items)):
        display.draw_menu(menu_items, i)
        time.sleep(2)
    
    display.clear()

def test_oled_text():
    print("测试 OLED 文本显示...")
    display = DisplayManager("OLED")
    
    # 测试清屏
    print("1. 清屏")
    display.clear()
    time.sleep(1)
    
    # 测试单行短文本
    print("2. 测试单行短文本")
    display.show_text_oled("你好!")
    time.sleep(2)
    
    # 测试多行短文本
    print("3. 测试多行短文本")
    display.show_text_oled("第一行\n第二行\n第三行")
    time.sleep(3)
    
    # 测试长文本自动换行和滚动
    print("4. 测试长文本自动换行和滚动")
    long_text = "这是一段很长的测试文本，用来测试OLED显示屏的自动换行和滚动显示功能。我们希望看到文本能够正确换行并通过滚动来显示完整内容。"
    display.show_text_oled(long_text, chars_per_line=8)
    time.sleep(1)  # 这里不需要延时，因为show_text_oled会自动控制滚动时间
    
    # 测试不同字体大小
    print("5. 测试不同字体大小")
    display.show_text_oled("大字体", font_size=16)
    time.sleep(2)
    display.show_text_oled("小字体", font_size=10)
    time.sleep(2)
    
    # 测试混合内容
    print("6. 测试混合内容")
    mixed_text = "标题\n这是正文内容\n第三行"
    display.show_text_oled(mixed_text, font_size=12)
    time.sleep(3)
    
    # 测试边界情况
    print("7. 测试边界情况")
    # 空字符串
    display.show_text_oled("")
    time.sleep(1)
    # 单个字符
    display.show_text_oled("测")
    time.sleep(1)
    # 多个换行
    display.show_text_oled("\n\n\n测试\n\n")
    time.sleep(2)
    
    display.clear()
    print("OLED 文本显示测试完成！")

def test_wait_for_button():
    """测试等待按钮的交互式文本显示"""
    print("测试等待按钮的交互式文本显示...")
    display = DisplayManager("OLED")
    controller = InputController()
    
    try:
        # 测试短文本
        print("1. 测试短文本")
        display.wait_for_button_with_text(
            controller,
            "这是一个测试\n按按钮1继续"
        )
        
        # 测试长文本
        print("2. 测试长文本")
        long_text = """这是一个很长的测试文本。
用来测试多行显示和滚动功能。
你可以使用摇杆上下移动来查看更多内容。
按按钮1继续下一步。
这是第五行文本。
这是第六行文本。
这是最后一行。"""
        display.wait_for_button_with_text(
            controller,
            long_text,
            chars_per_line=9
        )
        
        # 测试边界情况
        print("3. 测试边界情况")
        display.wait_for_button_with_text(
            controller,
            "单行文本测试"
        )
        
        print("等待按钮测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        controller.cleanup()
        display.clear()

if __name__ == "__main__":
    try:
        print("开始显示屏测试...")
        print("\n=== 等待按钮测试 ===")
        test_wait_for_button()
        print("\n测试完成！")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        print("清理完成") 