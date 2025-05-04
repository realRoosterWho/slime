from button_utils import InputController
from display_utils import DisplayManager
import time
import signal
import sys
import subprocess
import os

class MenuSystem:
    def __init__(self):
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
            "使用默认wifi",
            "使用热点wifi",
            "进入漂流",
            "系统信息",
            "退出漂流"
        ]
        self.current_selection = 0  # 当前选择的索引
        
        # 注册输入回调
        self.controller.register_joystick_callback('UP', self.on_up)
        self.controller.register_joystick_callback('DOWN', self.on_down)
        self.controller.register_button_callback('BTN1', self.on_confirm, 'press')
        
        # 显示初始菜单
        self.display_menu()
    
    def on_up(self):
        """向上选择"""
        if self.current_selection > 0:
            self.current_selection -= 1
            self.display_menu()
    
    def on_down(self):
        """向下选择"""
        if self.current_selection < len(self.menu_items) - 1:
            self.current_selection += 1
            self.display_menu()
    
    def run_openai_test(self):
        """运行OpenAI测试程序"""
        try:
            # 清理当前资源
            self.controller.cleanup()
            self.oled.clear()
            
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
    
    def connect_wifi(self, wifi_config):
        """连接WiFi的通用方法"""
        try:
            ssid = wifi_config['ssid']
            password = wifi_config['password']
            
            self.oled.show_text_oled(f"正在连接:\n{ssid}")
            
            # 创建wpa_supplicant配置
            wpa_config = (
                'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n'
                'update_config=1\n'
                'country=CN\n'
                '\n'
                'network={\n'
                f'    ssid="{ssid}"\n'
                f'    psk="{password}"\n'
                '    key_mgmt=WPA-PSK\n'
                '}\n'
            )
            
            # 写入配置文件
            with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
                f.write(wpa_config)
            
            # 重启WiFi接口
            subprocess.run(['sudo', 'ifconfig', 'wlan0', 'down'], check=True)
            subprocess.run(['sudo', 'ifconfig', 'wlan0', 'up'], check=True)
            subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'], check=True)
            
            # 等待连接
            time.sleep(5)
            
            # 检查连接状态
            result = subprocess.run(['iwgetid'], capture_output=True, text=True)
            if ssid in result.stdout:
                self.oled.show_text_oled(f"已连接到:\n{ssid}")
                print(f"成功连接到 {ssid}")
            else:
                self.oled.show_text_oled("连接失败")
                print("WiFi连接失败")
            
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

    def on_confirm(self):
        """确认选择"""
        selected_item = self.menu_items[self.current_selection]
        if selected_item == "进入漂流":
            self.oled.show_text_oled("正在启动漂流...")
            time.sleep(1)
            self.run_openai_test()
            self.display_menu()
        elif selected_item == "使用默认wifi":
            self.connect_default_wifi()
        elif selected_item == "使用热点wifi":
            self.connect_hotspot_wifi()
        elif selected_item == "系统信息":
            self.show_system_info()
        else:  # 退出漂流
            self.oled.show_text_oled("再见！")
            time.sleep(1)
            self.cleanup()
            sys.exit(0)
    
    def display_menu(self):
        """显示菜单"""
        menu_text = ""
        for i, item in enumerate(self.menu_items):
            # 当前选中的项目前面加上 ">"
            prefix = "> " if i == self.current_selection else "  "
            menu_text += f"{prefix}{item}\n"
        self.oled.show_text_oled(menu_text)
    
    def run(self):
        """运行菜单系统"""
        try:
            print("菜单系统运行中...")
            print("使用上下摇杆选择，按钮1确认")
            print("按 Ctrl+C 退出")
            
            while True:
                self.controller.check_inputs()
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        self.controller.cleanup()
        self.oled.clear()
        print("已清理所有资源")

def signal_handler(signum, frame):
    """信号处理函数"""
    print("\n🛑 检测到中断信号，正在清理...")
    if 'menu' in globals():
        menu.cleanup()
    sys.exit(0)

if __name__ == "__main__":
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        menu = MenuSystem()
        menu.run()
    except Exception as e:
        print(f"错误: {e}")
        if 'menu' in globals():
            menu.cleanup() 