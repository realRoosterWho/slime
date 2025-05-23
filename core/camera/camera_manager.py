import subprocess
import os

def run_camera_test():
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 拼接camera_test.py的完整路径
    camera_script = os.path.join(current_dir, "./camera_test.py")

    # 调用camera_test.py
    try:
        print("启动拍照脚本...")
        subprocess.run(["/usr/bin/python3", camera_script], check=True)
        print("拍照完成。")
    except subprocess.CalledProcessError as e:
        print(f"拍照脚本运行出错: {e}")

if __name__ == "__main__":
    run_camera_test()