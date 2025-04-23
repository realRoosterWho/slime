import subprocess
import sys
import time
import re

REQUIREMENTS = [
    "picamera2",
    "libcamera",
    "v4l2",
    "av",
    "prctl",
    "numpy",
    "pillow",
    "opencv",
    "simplejpeg"
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
        return True
    except subprocess.CalledProcessError:
        print(f"⚠️ mamba 安装 {module} 失败，尝试使用 pip 安装...")
        try:
            subprocess.run(["pip", "install", module], check=True)
            return True
        except subprocess.CalledProcessError:
            print(f"⚠️ pip 安装 {module} 也失败了，请手动检查。")
            return False

def find_missing_module(error_output):
    for r in REQUIREMENTS:
        if f"No module named '{r}'" in error_output:
            return r
    
    match = re.search(r"No module named '([^']+)'", error_output)
    if match:
        return match.group(1)
    
    return None

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
                print(output)
                
                missing = find_missing_module(output)
                if missing:
                    print(f"\n[*] 检测到缺失模块：{missing}")
                    if install_module(missing):
                        print(f"✅ 成功安装 {missing}")
                        time.sleep(1)
                    else:
                        print(f"❌ 无法安装 {missing}，请手动安装")
                        break
                else:
                    print("❗ 出现未知错误，终止。")
                    break
        except KeyboardInterrupt:
            print("\n用户中断。")
            break
