from display_utils import DisplayManager
import time

def test_lcd():
    print("测试LCD显示屏...")
    display = DisplayManager("LCD")
    
    # 测试清屏
    print("1. 测试清屏")
    display.clear()
    time.sleep(10)
    
    # 测试显示文本
    print("2. 测试显示文本")
    display.show_text("Hello Slime!", font_size=30)
    time.sleep(10)
    
    # 测试显示图片
    print("3. 测试显示图片")
    try:
        display.show_image("slime1.png")
        time.sleep(10)
    except:
        print("未找到图片文件，跳过图片测试")
    
    # 测试进度条
    print("4. 测试进度条")
    for i in range(11):
        display.draw_progress_bar(i/10)
        time.sleep(2)
    
    # 测试菜单
    print("5. 测试菜单")
    menu_items = ["选项1", "选项2", "选项3", "选项4"]
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
    time.sleep(10)
    
    # 测试显示文本
    print("2. 测试显示文本")
    display.show_text("Hello Slime!", font_size=12)
    time.sleep(10)
    
    # 测试进度条
    print("3. 测试进度条")
    for i in range(11):
        display.draw_progress_bar(i/10)
        time.sleep(2)
    
    # 测试菜单
    print("4. 测试菜单")
    menu_items = ["选项1", "选项2", "选项3"]
    for i in range(len(menu_items)):
        display.draw_menu(menu_items, i)
        time.sleep(2)
    
    display.clear()

if __name__ == "__main__":
    try:
        print("开始显示屏测试...")
        print("\n=== LCD测试 ===")
        # test_lcd()
        print("\n=== OLED测试 ===")
        test_oled()
        print("\n测试完成！")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        print("清理完成") 