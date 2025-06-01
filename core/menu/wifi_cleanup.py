#!/usr/bin/env python3
"""
WiFi连接清理工具
独立运行，用于清理临时WiFi连接，避免阻塞主程序退出
"""

import subprocess
import sys
import time
import os

def cleanup_temp_wifi_connections():
    """清理临时WiFi连接"""
    print("🔧 开始清理临时WiFi连接...")
    
    # 要清理的临时连接名模式
    temp_patterns = [
        "ShanghaiTech-temp",
        "RW_1963-temp", 
        "RW-temp"
    ]
    
    for pattern in temp_patterns:
        try:
            print(f"检查临时连接: {pattern}")
            # 检查连接是否存在
            check_result = subprocess.run([
                'sudo', 'nmcli', 'connection', 'show', pattern
            ], check=False, capture_output=True, text=True, timeout=5)
            
            if check_result.returncode == 0:
                print(f"找到临时连接: {pattern}，正在删除...")
                # 删除连接
                delete_result = subprocess.run([
                    'sudo', 'nmcli', 'connection', 'delete', pattern
                ], check=False, capture_output=True, text=True, timeout=10)
                
                if delete_result.returncode == 0:
                    print(f"✅ 已删除临时连接: {pattern}")
                else:
                    print(f"⚠️ 删除临时连接失败: {pattern}")
            else:
                print(f"未找到临时连接: {pattern}")
                
        except subprocess.TimeoutExpired:
            print(f"⚠️ 清理连接 {pattern} 超时")
        except Exception as e:
            print(f"⚠️ 清理连接 {pattern} 出错: {e}")
    
    print("✅ WiFi连接清理完成")

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--background":
        # 后台模式：延迟执行清理
        print("WiFi清理器启动（后台模式）")
        time.sleep(2)  # 等待主程序退出
        cleanup_temp_wifi_connections()
    else:
        # 前台模式：立即执行清理
        print("WiFi清理器启动（前台模式）")
        cleanup_temp_wifi_connections()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 WiFi清理器被中断")
    except Exception as e:
        print(f"❌ WiFi清理器出错: {e}") 