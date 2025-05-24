from core.input.button_utils import InputController
from core.display.display_utils import DisplayManager
from adafruit_ssd1306 import SSD1306_I2C
import time
import signal
import sys
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO  # 添加GPIO导入

class MenuSystem:
    def __init__(self):
        # 初始化GPIO设置（必须在最开始）
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            print("✅ GPIO已初始化为BCM模式")
        except Exception as e:
            print(f"⚠️ GPIO初始化警告: {e}")
        
        # 添加指示器帧计数（移到最前面）
        self.indicator_frame = 0
        self.should_exit = False  # 将退出标志移到类内部
        
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
        self.lcd = DisplayManager("LCD")  # 添加LCD显示管理器
        
        # 初始化输入控制器
        self.controller = InputController()
        
        # 菜单选项
        self.menu_items = [
            "开始漂流",      # derive_test.py
            "功能测试",      # openai_test.py (原漂流测试)
            "扫描可用wifi",
            "使用默认wifi",
            "使用热点wifi",
            "查看当前wifi",
            "系统信息",
            "重启系统",
            "关闭系统",
            "退出系统"
        ]
        
        # 在LCD上显示logo
        self.show_logo_on_lcd()
        
        # 注册输入回调
        self.controller.register_joystick_callback('UP', self.on_up)
        self.controller.register_joystick_callback('DOWN', self.on_down)
        self.controller.register_button_callback('BTN1', self.on_confirm, 'press')
        
        # 显示初始菜单
        self.display_menu()
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def show_logo_on_lcd(self):
        """在LCD上显示logo"""
        try:
            from PIL import Image
            
            # logo文件路径
            logo_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "assets", "images", "logo.png"
            )
            
            if os.path.exists(logo_path):
                # 加载logo图像
                logo_image = Image.open(logo_path)
                
                # 旋转图像180度以解决颠倒问题
                #rotated_logo = logo_image.rotate(180, expand=True)
                
                # 显示旋转后的logo
                self.lcd.show_image(rotated_logo)
                print(f"✅ Logo已显示在LCD上（已旋转180度）: {logo_path}")
            else:
                print(f"⚠️ Logo文件未找到: {logo_path}")
                # 显示默认的文本logo
                self.lcd.show_text("Cyberive\n\n史莱姆漂流\n系统")
                
        except Exception as e:
            print(f"❌ 显示logo时出错: {e}")
            try:
                # 备用方案：显示文本
                self.lcd.show_text("Cyberive\n\n史莱姆漂流\n系统")
            except Exception as fallback_error:
                print(f"❌ 备用logo显示也失败: {fallback_error}")

    def signal_handler(self, signum, frame):
        """信号处理函数"""
        print("\n🛑 检测到退出信号，准备退出...")
        self.should_exit = True
    
    def on_up(self):
        """向上选择"""
        if self.oled.menu_up():
            self.display_menu()
            time.sleep(0.2)
    
    def on_down(self):
        """向下选择"""
        if self.oled.menu_down(len(self.menu_items)):
            self.display_menu()
            time.sleep(0.2)
    
    def run_derive_test(self):
        """运行漂流程序 - 使用新架构"""
        try:
            # 清理当前资源
            self.controller.cleanup()
            self.oled.show_loading("正在启动漂流...")
            
            # 获取新启动脚本的路径
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            new_derive_script = os.path.join(current_dir, "start_new_derive.py")
            
            # 检查新启动脚本是否存在
            if not os.path.exists(new_derive_script):
                # 如果新脚本不存在，回退到旧版本
                self.oled.show_text_oled("新版本不可用\n使用旧版本")
                time.sleep(2)
                derive_script = os.path.join(current_dir, "core", "derive", "derive_test.py")
            else:
                derive_script = new_derive_script
            
            # 运行漂流程序
            print(f"启动漂流程序: {derive_script}")
            result = subprocess.run([sys.executable, derive_script], check=False)
            
            # 检查退出码
            if result.returncode == 42:
                print("检测到长按返回菜单")
            elif result.returncode == 0:
                print("漂流程序正常结束")
            else:
                print(f"漂流程序异常结束，退出码: {result.returncode}")
                self.oled.show_text_oled("程序异常结束")
                time.sleep(2)
            
        except subprocess.CalledProcessError as e:
            print(f"漂流程序运行出错: {e}")
            self.oled.show_text_oled("启动失败")
            time.sleep(2)
        except Exception as e:
            print(f"发生错误: {e}")
            self.oled.show_text_oled("发生错误")
            time.sleep(2)
        finally:
            # 重新初始化资源
            self.safe_reinitialize()
            print("返回主菜单")

    def run_openai_test(self):
        """运行功能测试程序"""
        try:
            # 清理当前资源
            self.controller.cleanup()
            self.oled.show_loading("正在启动功能测试...")
            
            # 获取openai_test.py的路径
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            openai_script = os.path.join(current_dir, "tests", "integration", "openai_test.py")
            
            # 运行openai_test.py
            print("启动功能测试程序...")
            subprocess.run([sys.executable, openai_script], check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"功能测试程序运行出错: {e}")
        except Exception as e:
            print(f"发生错误: {e}")
        finally:
            # 重新初始化资源
            self.safe_reinitialize()
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
        if selected_item == "开始漂流":
            self.run_derive_test()
        elif selected_item == "功能测试":
            self.run_openai_test()
        elif selected_item == "扫描可用wifi":
            self.scan_wifi()
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
        else:  # 退出系统
            self.oled.show_message("再见！")
            self.cleanup()
            sys.exit(0)
    
    def display_menu(self):
        """显示菜单"""
        self.oled.show_menu(self.menu_items)
    
    def run_step(self):
        """执行一次主循环"""
        if self.should_exit:
            return False
        self.controller.check_inputs()
        self.display_menu()  # 刷新显示
        time.sleep(0.1)  # 避免CPU占用过高
        return True
    
    def cleanup(self):
        """清理资源"""
        try:
            self.controller.cleanup()
            self.oled.show_text_oled("再见！")
            time.sleep(0.5)
            self.oled.clear()
            
            # 清理LCD显示
            if hasattr(self, 'lcd'):
                try:
                    self.lcd.clear()
                    print("✅ LCD已清理")
                except Exception as lcd_error:
                    print(f"⚠️ LCD清理失败: {lcd_error}")
            
            # 清理GPIO（参考derive的方式）
            try:
                GPIO.cleanup()
                print("✅ GPIO已清理")
            except Exception as gpio_error:
                print(f"⚠️ GPIO清理失败: {gpio_error}")
            
            print("已清理所有资源")
        except Exception as e:
            print(f"清理时出错: {e}")

    def show_long_text(self, text):
        """显示长文本，支持摇杆控制"""
        text_controller = self.oled.show_text_oled_interactive(text)
        text_controller['draw']()  # 显示第一页
        
        # 注册临时的摇杆回调
        original_up = self.controller.joystick_callbacks.get('UP')
        original_down = self.controller.joystick_callbacks.get('DOWN')
        
        def on_up():
            if text_controller['up']():
                text_controller['draw']()
                time.sleep(0.2)
        
        def on_down():
            if text_controller['down']():
                text_controller['draw']()
                time.sleep(0.2)
        
        self.controller.register_joystick_callback('UP', on_up)
        self.controller.register_joystick_callback('DOWN', on_down)
        
        # 等待按钮1被按下
        while not self.should_exit:
            self.controller.check_inputs()
            time.sleep(0.1)
        
        # 恢复原来的回调
        self.controller.register_joystick_callback('UP', original_up)
        self.controller.register_joystick_callback('DOWN', original_down)

    def safe_reinitialize(self):
        """安全的重新初始化方法，避免GPIO冲突"""
        try:
            print("🔄 正在重新初始化菜单系统...")
            
            # 不重新初始化GPIO，只重新初始化其他组件
            self.oled = DisplayManager("OLED")
            self.lcd = DisplayManager("LCD")
            self.controller = InputController()
            
            # 重新显示logo
            self.show_logo_on_lcd()
            
            # 重新注册输入回调
            self.controller.register_joystick_callback('UP', self.on_up)
            self.controller.register_joystick_callback('DOWN', self.on_down)
            self.controller.register_button_callback('BTN1', self.on_confirm, 'press')
            
            # 显示菜单
            self.display_menu()
            
            print("✅ 菜单系统重新初始化完成")
            
        except Exception as e:
            print(f"❌ 重新初始化失败: {e}")
            # 备用方案：完全重新初始化
            try:
                self.__init__()
            except Exception as fallback_error:
                print(f"❌ 备用初始化也失败: {fallback_error}")

if __name__ == "__main__":
    try:
        menu = MenuSystem()
        print("菜单系统运行中...")
        print("使用上下摇杆选择，按钮1确认")
        print("按 Ctrl+C 退出")
        
        while menu.run_step():
            pass
            
        print("🧹 正在清理...")
        menu.cleanup()
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        if 'menu' in globals():
            try:
                menu.cleanup()
            except Exception:
                pass
        sys.exit(1)