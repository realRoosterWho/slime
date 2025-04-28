from display_utils import DisplayManager
import time

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

if __name__ == "__main__":
    try:
        print("开始显示屏测试...")
        print("\n=== LCD测试 ===")
        test_lcd()
        print("\n=== OLED测试 ===")
        test_oled()
        print("\n测试完成！")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        print("清理完成") 