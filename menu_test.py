from button_utils import InputController
from display_utils import DisplayManager
from adafruit_ssd1306 import SSD1306_I2C
import time
import signal
import sys
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

class MenuSystem:
    def __init__(self):
        # 添加指示器帧计数（移到最前面）
        self.indicator_frame = 0
        
        # WiFi配置
        self.wifi_configs = {
            'default': {
                'ssid': 'RW_1963',
                'password': '11111111'
            },
            'hotspot': {
                'ssid': 'RW',
                'password': '23333333'
            }
        }
        
        # 初始化显示
        self.oled = DisplayManager("OLED")
        
        # 初始化输入控制器
        self.controller = InputController()
        
        # 菜单选项
        self.menu_items = [
            "扫描可用wifi",
            "使用默认wifi",
            "使用热点wifi",
            "查看当前wifi",
            "进入漂流",
            "系统信息",
            "重启系统",
            "关闭系统",
            "退出漂流"
        ]
        
        # 注册输入回调
        self.controller.register_joystick_callback('UP', self.on_up)
        self.controller.register_joystick_callback('DOWN', self.on_down)
        self.controller.register_button_callback('BTN1', self.on_confirm, 'press')
        
        # 显示初始菜单
        self.display_menu()
    
    def on_up(self):
        """向上选择"""
        if self.oled.menu_up():
            self.display_menu()
            time.sleep(0.5)
    
    def on_down(self):
        """向下选择"""
        if self.oled.menu_down(len(self.menu_items)):
            self.display_menu()
            time.sleep(0.5)
    
    def run_openai_test(self):
        """运行OpenAI测试程序"""
        try:
            # 清理当前资源
            self.controller.cleanup()
            self.oled.show_loading("正在启动漂流...")
            
            # 获取openai_test.py的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            openai_script = os.path.join(current_dir, "openai_test.py")
            
            # 运行openai_test.py
            print("启动漂流程序...")
            subprocess.run([sys.executable, openai_script], check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"漂流程序运行出错: {e}")
        except Exception as e:
            print(f"发生错误: {e}")
        finally:
            # 重新初始化资源
            self.__init__()
            print("返回主菜单")
    
    def get_current_wifi(self):
        """获取当前连接的WiFi名称"""
        try:
            result = subprocess.run(['iwgetid'], capture_output=True, text=True)
            if result.stdout:
                # iwgetid输出格式: wlan0    ESSID:"WiFi名称"
                ssid = result.stdout.split('ESSID:')[1].strip().strip('"')
                return ssid
            return None
        except Exception:
            return None

    def show_current_wifi(self):
        """显示当前WiFi连接状态"""
        try:
            current_wifi = self.get_current_wifi()
            if current_wifi:
                self.oled.show_text_oled(f"当前WiFi:\n{current_wifi}")
            else:
                self.oled.show_text_oled("未连接WiFi")
            time.sleep(2)
        finally:
            self.display_menu()

    def disconnect_wifi(self):
        """断开当前WiFi连接"""
        try:
            subprocess.run(['sudo', 'killall', 'wpa_supplicant'], check=False)
            subprocess.run(['sudo', 'ifconfig', 'wlan0', 'down'], check=True)
            time.sleep(1)
            subprocess.run(['sudo', 'ifconfig', 'wlan0', 'up'], check=True)
            time.sleep(1)
        except Exception as e:
            print(f"断开WiFi错误: {e}")

    def scan_wifi(self):
        """扫描可用的WiFi网络"""
        try:
            self.oled.show_text_oled("正在扫描...")
            
            # 使用nmcli扫描WiFi
            subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'rescan'], check=True)
            time.sleep(2)  # 等待扫描完成
            
            # 获取扫描结果
            result = subprocess.run(
                ['sudo', 'nmcli', '-t', '-f', 'SSID', 'device', 'wifi', 'list'],
                capture_output=True,
                text=True
            )
            
            # 解析扫描结果
            networks = []
            for line in result.stdout.split('\n'):
                if line and line not in networks:  # 去除重复的SSID
                    networks.append(line)
            
            if networks:
                # 显示找到的网络
                self.show_networks(networks)
            else:
                self.oled.show_text_oled("未找到网络")
                time.sleep(2)
                self.display_menu()
                
        except Exception as e:
            print(f"扫描错误: {e}")
            self.oled.show_text_oled("扫描失败")
            time.sleep(2)
            self.display_menu()

    def show_networks(self, networks):
        """显示找到的网络列表"""
        self.network_list = networks
        self.network_selection = 0
        self.display_networks()

    def display_networks(self):
        """显示网络列表"""
        total_networks = len(self.network_list)
        if total_networks <= 3:
            start_idx = 0
            end_idx = total_networks
        else:
            if self.network_selection == 0:
                start_idx = 0
                end_idx = 3
            elif self.network_selection == total_networks - 1:
                start_idx = total_networks - 3
                end_idx = total_networks
            else:
                start_idx = self.network_selection - 1
                end_idx = self.network_selection + 2

        network_text = ""
        for i in range(start_idx, end_idx):
            prefix = "> " if i == self.network_selection else "  "
            network_text += f"{prefix}{self.network_list[i]}\n"
        network_text = network_text.rstrip()
        self.oled.show_text_oled(network_text)

    def connect_wifi(self, wifi_config):
        """连接WiFi的通用方法"""
        try:
            ssid = wifi_config['ssid']
            password = wifi_config['password']
            
            self.oled.show_text_oled(f"正在连接:\n{ssid}")
            
            # 使用nmcli连接WiFi
            try:
                # 先断开当前连接
                subprocess.run(['sudo', 'nmcli', 'device', 'disconnect', 'wlan0'], check=False)
                time.sleep(1)
                
                # 删除可能存在的同名连接
                subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], check=False)
                time.sleep(1)
                
                # 添加并激活新连接
                subprocess.run([
                    'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
                    'password', password,
                    'ifname', 'wlan0'
                ], check=True)
                
                # 等待连接
                attempts = 0
                max_attempts = 3
                while attempts < max_attempts:
                    time.sleep(3)
                    current_wifi = self.get_current_wifi()
                    if current_wifi == ssid:
                        self.oled.show_text_oled(f"已连接到:\n{ssid}")
                        print(f"成功连接到 {ssid}")
                        break
                    attempts += 1
                    if attempts < max_attempts:
                        print(f"重试连接... ({attempts}/{max_attempts})")
                else:
                    self.oled.show_text_oled("连接失败")
                    print("WiFi连接失败")
                
            except Exception as e:
                print(f"NetworkManager连接错误: {e}")
                self.oled.show_text_oled("连接失败")
            
            time.sleep(2)
            
        except Exception as e:
            self.oled.show_text_oled("连接出错")
            print(f"WiFi连接错误: {e}")
            time.sleep(2)
        finally:
            self.display_menu()

    def connect_default_wifi(self):
        """连接默认WiFi"""
        self.connect_wifi(self.wifi_configs['default'])

    def connect_hotspot_wifi(self):
        """连接热点WiFi"""
        self.connect_wifi(self.wifi_configs['hotspot'])

    def show_system_info(self):
        """显示系统信息"""
        try:
            import psutil
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            info_text = f"CPU: {cpu_usage}%\nRAM: {memory.percent}%"
            self.oled.show_text_oled(info_text)
            time.sleep(3)
        except Exception as e:
            self.oled.show_text_oled("获取系统信息失败")
            print(f"系统信息错误: {e}")
            time.sleep(1)
        finally:
            self.display_menu()

    def system_reboot(self):
        """重启系统"""
        try:
            self.oled.show_message("系统正在重启...")
            self.cleanup()
            subprocess.run(['sudo', 'reboot'], check=True)
        except Exception as e:
            print(f"重启错误: {e}")
            self.oled.show_message("重启失败!")
            self.display_menu()

    def system_shutdown(self):
        """关闭系统"""
        try:
            self.oled.show_message("系统正在关闭...")
            self.cleanup()
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
        except Exception as e:
            print(f"关机错误: {e}")
            self.oled.show_message("关机失败!")
            self.display_menu()

    def on_confirm(self):
        """确认选择"""
        selected_index = self.oled.get_selected_index()
        selected_item = self.menu_items[selected_index]
        if selected_item == "扫描可用wifi":
            self.scan_wifi()
        elif selected_item == "进入漂流":
            self.run_openai_test()
        elif selected_item == "使用默认wifi":
            self.connect_default_wifi()
        elif selected_item == "使用热点wifi":
            self.connect_hotspot_wifi()
        elif selected_item == "查看当前wifi":
            self.show_current_wifi()
        elif selected_item == "系统信息":
            self.show_system_info()
        elif selected_item == "重启系统":
            self.system_reboot()
        elif selected_item == "关闭系统":
            self.system_shutdown()
        else:  # 退出漂流
            self.oled.show_message("再见！")
            self.cleanup()
            sys.exit(0)
    
    def display_menu(self):
        """显示菜单"""
        self.oled.show_menu(self.menu_items)
    
    def run(self):
        """运行菜单系统"""
        try:
            print("菜单系统运行中...")
            print("使用上下摇杆选择，按钮1确认")
            print("按 Ctrl+C 退出")
            
            while True:
                self.controller.check_inputs()
                time.sleep(0.1)  # 只需要检查输入，不需要在这里刷新显示
                
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        self.controller.cleanup()
        self.oled.clear()
        print("已清理所有资源")

def cleanup_handler(signum, frame):
    """处理 systemd 服务停止信号"""
    print("\n🛑 收到 systemd 停止信号，正在清理...")
    if 'menu' in globals():
        menu.oled.show_text_oled("系统正在停止...")
        time.sleep(1)
        menu.cleanup()
    sys.exit(0)

def signal_handler(signum, frame):
    """处理用户中断信号(Ctrl+C)"""
    print("\n🛑 检测到用户中断，正在清理...")
    if 'menu' in globals():
        menu.oled.show_text_oled("正在退出...")
        time.sleep(1)
        menu.cleanup()
    sys.exit(0)

if __name__ == "__main__":
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)    # Ctrl+C
    signal.signal(signal.SIGTERM, cleanup_handler)  # systemd 停止信号
    
    try:
        menu = MenuSystem()
        menu.run()
    except Exception as e:
        print(f"错误: {e}")
        if 'menu' in globals():
            menu.oled.show_text_oled("发生错误\n正在退出...")
            time.sleep(1)
            menu.cleanup()
        sys.exit(1) 