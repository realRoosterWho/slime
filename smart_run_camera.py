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
    "simplejpeg",
    "kms"  # 添加kms模块
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
    # 检查直接缺失的模块
    for r in REQUIREMENTS:
        if f"No module named '{r}'" in error_output:
            return r
    
    # 检查深层依赖
    match = re.search(r"No module named '([^']+)'", error_output)
    if match:
        return match.group(1)
    
    # 检查属性错误
    attr_match = re.search(r"module '([^']+)' has no attribute '([^']+)'", error_output)
    if attr_match:
        module_name = attr_match.group(1)
        print(f"\n[*] 检测到模块 {module_name} 的属性错误")
        # 尝试重新安装该模块
        return module_name
    
    return None

def handle_error(error_output):
    # 检查是否是属性错误
    attr_match = re.search(r"module '([^']+)' has no attribute '([^']+)'", error_output)
    if attr_match:
        module_name = attr_match.group(1)
        attribute_name = attr_match.group(2)
        print(f"\n[*] 检测到模块 {module_name} 缺少属性 {attribute_name}")
        print(f"[*] 尝试重新安装 {module_name}...")
        return module_name
    
    # 检查其他类型的错误
    error_patterns = [
        (r"ImportError: ([^\n]+)", "导入错误"),
        (r"AttributeError: ([^\n]+)", "属性错误"),
        (r"ModuleNotFoundError: ([^\n]+)", "模块未找到"),
        (r"NameError: ([^\n]+)", "名称错误")
    ]
    
    for pattern, error_type in error_patterns:
        match = re.search(pattern, error_output)
        if match:
            print(f"\n[*] 检测到{error_type}: {match.group(1)}")
            # 尝试从错误信息中提取模块名
            module_match = re.search(r"module '([^']+)'", match.group(1))
            if module_match:
                return module_match.group(1)
    
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
                print(output)  # 打印错误信息以便调试
                
                # 首先尝试处理属性错误
                module_to_install = handle_error(output)
                if module_to_install:
                    print(f"\n[*] 尝试重新安装模块：{module_to_install}")
                    if install_module(module_to_install):
                        print(f"✅ 成功安装 {module_to_install}")
                        time.sleep(1)
                        continue
                    else:
                        print(f"❌ 无法安装 {module_to_install}，请手动检查")
                        break
                
                # 如果没有找到要安装的模块，检查是否是其他类型的错误
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
