from display_utils import DisplayManager
import time
import os
import signal
import sys

def cleanup_handler(signum, frame):
    """清理资源并优雅退出"""
    print("\n🛑 检测到中断信号，正在清理资源...")
    try:
        if 'lcd_display' in globals():
            lcd_display.clear()
        print("✅ 已清理显示资源")
    except:
        pass
    sys.exit(0)

def main():
    # 设置信号处理
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        # 初始化LCD显示器（使用BitBang模式）
        print("初始化LCD显示器...")
        lcd_display = DisplayManager("LCD")
        
        # 获取current_image.jpg的路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "current_image.jpg")
        
        if os.path.exists(image_path):
            print(f"显示图片: {image_path}")
            lcd_display.show_image(image_path)
            print("图片显示成功")
            
            # 保持显示直到按Ctrl+C
            print("\n图片显示中... 按 Ctrl+C 退出")
            while True:
                time.sleep(1)
        else:
            print(f"错误: 找不到图片文件 {image_path}")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'lcd_display' in globals():
            lcd_display.clear()
            print("已清理显示")

if __name__ == "__main__":
    main()