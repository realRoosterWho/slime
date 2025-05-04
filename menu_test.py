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
            
            # 确保WiFi接口启动
            subprocess.run(['sudo', 'ifconfig', 'wlan0', 'up'], check=True)
            
            # 扫描WiFi
            result = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'], 
                                 capture_output=True, text=True)
            
            # 解析扫描结果
            networks = []
            for line in result.stdout.split('\n'):
                if 'ESSID:' in line:
                    ssid = line.split('ESSID:')[1].strip().strip('"')
                    if ssid:  # 排除隐藏网络
                        networks.append(ssid)
            
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
            
            # 先断开当前连接
            self.disconnect_wifi()
            
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
                '    scan_ssid=1\n'
                '}\n'
            )
            
            # 写入配置文件
            with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
                f.write(wpa_config)
            
            # 重启网络服务
            subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'], check=True)
            subprocess.run(['sudo', 'systemctl', 'restart', 'dhcpcd'], check=True)
            
            # 等待连接
            attempts = 0
            while attempts < 3:
                time.sleep(5)
                current_wifi = self.get_current_wifi()
                if current_wifi == ssid:
                    self.oled.show_text_oled(f"已连接到:\n{ssid}")
                    print(f"成功连接到 {ssid}")
                    break
                attempts += 1
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

    def system_reboot(self):
        """重启系统"""
        try:
            self.oled.show_text_oled("系统正在重启...")
            time.sleep(1)
            self.cleanup()
            subprocess.run(['sudo', 'reboot'], check=True)
        except Exception as e:
            self.oled.show_text_oled("重启失败!")
            print(f"重启错误: {e}")
            time.sleep(2)
            self.display_menu()

    def system_shutdown(self):
        """关闭系统"""
        try:
            self.oled.show_text_oled("系统正在关闭...")
            time.sleep(1)
            self.cleanup()
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
        except Exception as e:
            self.oled.show_text_oled("关机失败!")
            print(f"关机错误: {e}")
            time.sleep(2)
            self.display_menu()

    def on_confirm(self):
        """确认选择"""
        selected_item = self.menu_items[self.current_selection]
        if selected_item == "扫描可用wifi":
            self.scan_wifi()
        elif selected_item == "进入漂流":
            self.oled.show_text_oled("正在启动漂流...")
            time.sleep(1)
            self.run_openai_test()
            self.display_menu()
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
            self.oled.show_text_oled("再见！")
            time.sleep(1)
            self.cleanup()
            sys.exit(0)
    
    def display_menu(self):
        """显示菜单"""
        # 计算显示范围
        total_items = len(self.menu_items)
        if self.current_selection >= total_items:
            self.current_selection = total_items - 1
        
        # 确定显示的起始和结束索引
        if total_items <= 3:
            # 如果总项目不超过3个，全部显示
            start_idx = 0
            end_idx = total_items
        else:
            # 如果超过3个，需要滚动显示
            if self.current_selection == 0:
                start_idx = 0
                end_idx = 3
            elif self.current_selection == total_items - 1:
                start_idx = total_items - 3
                end_idx = total_items
            else:
                start_idx = self.current_selection - 1
                end_idx = self.current_selection + 2
        
        # 生成显示文本
        menu_text = ""
        for i in range(start_idx, end_idx):
            prefix = "> " if i == self.current_selection else "  "
            menu_text += f"{prefix}{self.menu_items[i]}\n"
        
        # 去掉最后的换行符
        menu_text = menu_text.rstrip()
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