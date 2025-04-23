import subprocess
import sys
import time

REQUIREMENTS = [
    "picamera2",
    "libcamera",
    "v4l2",
    "av",
    "prctl",
    "numpy",
    "pillow",
    "opencv"
]

def try_run():
    try:
        subprocess.run(["python3", "camera_test.py"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("\n❌ 程序运行失败！")
        return False
    except ModuleNotFoundError as e:
        print(f"\n❌ 缺失模块：{e.name}")
        return e.name

def install_module(module):
    print(f"\n[*] 正在尝试用 mamba 安装缺失模块：{module}")
    try:
        subprocess.run(["mamba", "install", module, "-c", "conda-forge", "-y"], check=True)
    except subprocess.CalledProcessError:
        print(f"⚠️ mamba 安装 {module} 失败，请手动检查。")

if __name__ == "__main__":
    print("🎬 启动 camera_test.py 并自动安装缺失模块...")
    while True:
        try:
            result = subprocess.run(["python3", "camera_test.py"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 成功运行 camera_test.py！")
                break
            else:
                output = result.stderr + result.stdout
                missing = None
                for r in REQUIREMENTS:
                    if f"No module named '{r}'" in output:
                        missing = r
                        break
                if missing:
                    install_module(missing)
                    time.sleep(1)
                else:
                    print(result.stdout)
                    print(result.stderr)
                    print("❗ 出现未知错误，终止。")
                    break
        except KeyboardInterrupt:
            print("\n用户中断。")
            break
