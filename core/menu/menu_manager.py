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
            },
            'campus': {
                'ssid': 'ShanghaiTech',
                'username': '2023551018',
                'password': 'Imissyou1224.',
                'type': 'enterprise'  # 标记为企业级WiFi
            }
        }
        
        # 记录临时连接配置名，用于程序退出时清理
        self.temp_connections = []
        
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
            "使用调试wifi",
            "使用热点wifi",
            "连接校园网",     # 新增：企业级WiFi连接
            "断开校园网",     # 新增：断开企业级WiFi并清理配置
            "查看当前wifi",
            "系统信息",
            "重启设备",
            "关闭设备",
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
                
                # 应用水平翻转（左右镜像）
                mirrored_logo = logo_image.transpose(Image.FLIP_LEFT_RIGHT)
                
                # 显示镜像后的logo
                self.lcd.show_image(mirrored_logo)
                print(f"✅ Logo已显示在LCD上（已水平镜像）: {logo_path}")
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
        """信号处理函数 - 优化版，快速退出"""
        print("\n🛑 检测到退出信号，正在快速退出...")
        self.should_exit = True
        
        # 调用统一的清理方法
        try:
            self.cleanup()
        except Exception as e:
            print(f"⚠️ 清理出错: {e}")
        
        print("👋 程序已快速退出")
        import os
        os._exit(0)  # 强制退出，避免卡死
    
    def on_up(self):
        """向上选择"""
        if self.should_exit:
            return
        if self.oled.menu_up():
            self.display_menu()
            time.sleep(0.2)
    
    def on_down(self):
        """向下选择"""
        if self.should_exit:
            return
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
                # 使用旧的运行方式
                result = subprocess.run([sys.executable, derive_script], check=False)
            else:
                derive_script = new_derive_script
                # 使用新的前台运行方式，不做缓冲
                print(f"启动漂流程序: {derive_script}")
                proc = subprocess.Popen(
                    [sys.executable, "-u", "start_new_derive.py"],
                    cwd=current_dir,
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )
                result_code = proc.wait()
                
                # 创建一个模拟的result对象来保持兼容性
                class MockResult:
                    def __init__(self, returncode):
                        self.returncode = returncode
                result = MockResult(result_code)
            
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
                # 直接显示WiFi列表供用户选择
                self.show_wifi_selection_list(networks)
            else:
                self.oled.wait_for_button_with_text(
                    self.controller,
                    "未找到WiFi网络\n\n请检查WiFi是否开启\n\n按任意键返回菜单"
                )
                self.display_menu()
                
        except Exception as e:
            print(f"扫描错误: {e}")
            self.oled.wait_for_button_with_text(
                self.controller,
                f"扫描失败\n\n{str(e)[:30]}...\n\n按任意键返回菜单"
            )
            self.display_menu()

    def show_wifi_selection_list(self, networks):
        """显示WiFi选择列表，使用wait_for_selection"""
        try:
            # 使用新的wait_for_selection功能
            selected_index = self.oled.wait_for_selection(
                self.controller,
                networks,
                title="选择WiFi"
            )
            
            if selected_index >= 0:
                # 用户选择了一个WiFi
                selected_wifi = networks[selected_index]
                print(f"用户选择了WiFi: {selected_wifi}")
                self.try_connect_selected_wifi(selected_wifi)
            else:
                # 用户取消选择，返回主菜单
                print("用户取消WiFi选择")
                self.display_menu()
                
        except Exception as e:
            print(f"WiFi选择出错: {e}")
            self.oled.wait_for_button_with_text(
                self.controller,
                f"选择出错\n\n{str(e)[:30]}...\n\n按任意键返回菜单"
            )
            self.display_menu()

    def wifi_selection_up(self):
        """WiFi选择向上 - 已移除，使用wait_for_selection代替"""
        pass

    def wifi_selection_down(self):
        """WiFi选择向下 - 已移除，使用wait_for_selection代替"""
        pass

    def wifi_selection_connect(self):
        """尝试连接选中的WiFi - 已移除，使用wait_for_selection代替"""
        pass

    def wifi_selection_exit(self):
        """退出WiFi选择模式 - 已移除，使用wait_for_selection代替"""
        pass

    def exit_wifi_selection(self):
        """退出WiFi选择模式 - 已移除，使用wait_for_selection代替"""
        pass

    def display_wifi_selection(self):
        """显示WiFi选择界面 - 已移除，使用wait_for_selection代替"""
        pass

    def try_connect_selected_wifi(self, selected_wifi):
        """尝试连接选中的WiFi"""
        try:
            default_password = "11111111"
            
            # 对所有WiFi都使用默认密码尝试连接
            confirm_text = f"您选择了WiFi:\n{selected_wifi}\n将使用默认密码:\n{default_password}\n进行连接\n\n请确保您的WiFi热点\n密码已设为此密码\n\n按BT1开始连接\n按BT2返回菜单"
            
            result = self.oled.wait_for_button_with_text(
                self.controller,
                confirm_text,
                font_size=10,
                chars_per_line=18,
                visible_lines=3
            )
            
            if hasattr(self.controller, 'last_button'):
                if self.controller.last_button == 'BTN1':
                    # 使用默认密码连接
                    self.safe_connect_wifi(selected_wifi, default_password)
                else:
                    self.display_menu()
            else:
                self.display_menu()
                
        except Exception as e:
            print(f"WiFi连接出错: {e}")
            self.oled.wait_for_button_with_text(
                self.controller,
                f"连接出错\n\n{str(e)[:30]}...\n\n按任意键返回菜单"
            )
            self.display_menu()

    def show_hotspot_connection_option(self, networks):
        """显示热点连接选项 - 已移除，改为直接显示WiFi列表"""
        pass

    def try_connect_mobile_hotspot(self):
        """尝试连接手机热点 - 已移除，改为在WiFi选择中处理"""
        pass

    def safe_connect_wifi(self, ssid, password):
        """安全的WiFi连接方法 - 失败时不会断开当前连接"""
        try:
            # 先获取当前连接信息作为备份
            current_wifi = self.get_current_wifi()
            
            self.oled.show_text_oled(f"正在连接:\n{ssid}\n\n请稍候...")
            
            # 使用更安全的连接方式：先尝试添加连接配置，不立即断开当前连接
            try:
                # 删除可能存在的旧临时连接
                subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], 
                             check=False, capture_output=True)
                time.sleep(0.5)
                
                # 尝试连接新WiFi（如果失败，当前连接仍然保持）
                connect_result = subprocess.run([
                    'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
                    'password', password,
                    'ifname', 'wlan0'
                ], check=False, capture_output=True, text=True)
                
                if connect_result.returncode == 0:
                    # 连接成功，等待验证
                    time.sleep(3)
                    new_wifi = self.get_current_wifi()
                    
                    if new_wifi == ssid:
                        self.oled.wait_for_button_with_text(
                            self.controller,
                            f"✅ 连接成功！\n\n当前WiFi:\n{ssid}\n\n临时连接模式\n程序退出时清理\n\n按任意键返回菜单"
                        )
                        print(f"成功连接到 {ssid}")
                    else:
                        self.oled.wait_for_button_with_text(
                            self.controller,
                            f"❌ 连接验证失败\n\n当前仍连接:\n{current_wifi or '未知'}\n\n按任意键返回菜单"
                        )
                        print("连接验证失败")
                else:
                    # 连接失败
                    error_msg = connect_result.stderr.strip() if connect_result.stderr else "未知错误"
                    self.oled.wait_for_button_with_text(
                        self.controller,
                        f"❌ 连接失败\n\n{error_msg[:20]}...\n\n当前WiFi保持不变:\n{current_wifi or '未连接'}\n\n按任意键返回菜单"
                    )
                    print(f"WiFi连接失败: {error_msg}")
                
            except Exception as e:
                self.oled.wait_for_button_with_text(
                    self.controller,
                    f"❌ 连接出错\n\n{str(e)[:20]}...\n\n当前WiFi保持不变\n\n按任意键返回菜单"
                )
                print(f"WiFi连接异常: {e}")
            
        except Exception as e:
            self.oled.wait_for_button_with_text(
                self.controller,
                f"连接过程出错\n\n{str(e)[:30]}...\n\n按任意键返回菜单"
            )
            print(f"WiFi连接过程出错: {e}")
        finally:
            # 返回主菜单
            self.display_menu()

    def safe_connect_enterprise_wifi(self, wifi_config):
        """安全的企业级WiFi连接方法 - 临时连接，不保存配置"""
        try:
            # 先获取当前连接信息作为备份
            current_wifi = self.get_current_wifi()
            
            ssid = wifi_config['ssid']
            username = wifi_config['username']
            password = wifi_config['password']
            
            self.oled.show_text_oled(f"正在连接:\n{ssid}\n\n临时连接模式\n不会保存配置")
            
            # 使用更安全的连接方式：临时连接
            try:
                # 使用企业级WiFi连接（WPA-EAP）
                # 第一步：创建企业级WiFi连接配置
                connection_name = f"{ssid}-temp"  # 使用临时连接名
                
                # 删除可能存在的同名连接和旧临时连接
                subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], 
                             check=False, capture_output=True)
                subprocess.run(['sudo', 'nmcli', 'connection', 'delete', connection_name], 
                             check=False, capture_output=True)
                time.sleep(0.5)
                
                create_result = subprocess.run([
                    'sudo', 'nmcli', 'connection', 'add',
                    'type', 'wifi',
                    'con-name', connection_name,
                    'ifname', 'wlan0',
                    'ssid', ssid,
                    'wifi-sec.key-mgmt', 'wpa-eap',
                    '802-1x.eap', 'peap',
                    '802-1x.phase2-auth', 'mschapv2',
                    '802-1x.identity', username,
                    '802-1x.password', password
                ], check=False, capture_output=True, text=True)
                
                if create_result.returncode == 0:
                    print(f"企业级WiFi配置创建成功: {connection_name}")
                    
                    # 第二步：激活连接
                    connect_result = subprocess.run([
                        'sudo', 'nmcli', 'connection', 'up', connection_name
                    ], check=False, capture_output=True, text=True)
                else:
                    print(f"企业级WiFi配置创建失败: {create_result.stderr}")
                    connect_result = create_result  # 使用创建结果作为连接结果
                
                if connect_result.returncode == 0:
                    # 连接成功，等待验证
                    time.sleep(5)  # 企业级WiFi需要更长的连接时间
                    new_wifi = self.get_current_wifi()
                    
                    if new_wifi == ssid:
                        print(f"成功连接到企业级WiFi {ssid}")
                        
                        # 🔑 关键：连接成功后不立即删除配置，记录临时配置名以便后续清理
                        self.temp_connections.append(connection_name)
                        
                        self.oled.wait_for_button_with_text(
                            self.controller,
                            f"✅ 连接成功！\n\n当前WiFi:\n{ssid}\n\n临时连接模式\n程序退出时清理\n\n按任意键返回菜单"
                        )
                    else:
                        self.oled.wait_for_button_with_text(
                            self.controller,
                            f"❌ 连接验证失败\n\n可能的原因：\n- 用户名或密码错误\n- 网络认证超时\n\n当前仍连接:\n{current_wifi or '未知'}\n\n按任意键返回菜单"
                        )
                        print("企业级WiFi连接验证失败")
                else:
                    # 连接失败
                    error_msg = connect_result.stderr.strip() if connect_result.stderr else "未知错误"
                    self.oled.wait_for_button_with_text(
                        self.controller,
                        f"❌ 连接失败\n\n{error_msg[:20]}...\n\n可能的原因：\n- 不在校园网范围内\n- 认证信息错误\n\n当前WiFi保持不变:\n{current_wifi or '未连接'}\n\n按任意键返回菜单"
                    )
                    print(f"企业级WiFi连接失败: {error_msg}")
                
            except Exception as e:
                self.oled.wait_for_button_with_text(
                    self.controller,
                    f"❌ 连接出错\n\n{str(e)[:20]}...\n\n当前WiFi保持不变\n\n按任意键返回菜单"
                )
                print(f"企业级WiFi连接异常: {e}")
            
        except Exception as e:
            self.oled.wait_for_button_with_text(
                self.controller,
                f"连接过程出错\n\n{str(e)[:30]}...\n\n按任意键返回菜单"
            )
            print(f"企业级WiFi连接过程出错: {e}")
        finally:
            # 返回主菜单
            self.display_menu()

    def show_networks(self, networks):
        """显示找到的网络列表 - 已移除，改为show_wifi_selection_list"""
        pass

    def connect_wifi(self, wifi_config):
        """连接WiFi的通用方法 - 支持普通和企业级WiFi"""
        if wifi_config.get('type') == 'enterprise':
            # 企业级WiFi使用专门的连接方法
            self.safe_connect_enterprise_wifi(wifi_config)
        else:
            # 普通WiFi使用原来的方法
            ssid = wifi_config['ssid']
            password = wifi_config['password']
            self.safe_connect_wifi(ssid, password)

    def connect_default_wifi(self):
        """连接默认WiFi"""
        self.connect_wifi(self.wifi_configs['default'])

    def connect_hotspot_wifi(self):
        """连接热点WiFi"""
        self.connect_wifi(self.wifi_configs['hotspot'])

    def connect_campus_wifi(self):
        """连接校园网（使用已配置的ShanghaiTech）"""
        try:
            current_wifi = self.get_current_wifi()
            
            self.oled.show_text_oled("正在连接校园网\nShanghaiTech")
            
            # 直接激活已存在的ShanghaiTech连接
            connect_result = subprocess.run([
                'sudo', 'nmcli', 'connection', 'up', 'ShanghaiTech'
            ], check=False, capture_output=True, text=True)
            
            if connect_result.returncode == 0:
                # 连接成功，等待验证
                time.sleep(3)  
                new_wifi = self.get_current_wifi()
                
                if new_wifi == 'ShanghaiTech':
                    self.oled.wait_for_button_with_text(
                        self.controller,
                        f"✅ 连接成功！\n\n当前WiFi:\nShanghaiTech\n\n按任意键返回菜单"
                    )
                    print("成功连接到校园网")
                else:
                    self.oled.wait_for_button_with_text(
                        self.controller,
                        f"❌ 连接验证失败\n\n当前仍连接:\n{current_wifi or '未知'}\n\n按任意键返回菜单"
                    )
                    print("校园网连接验证失败")
            else:
                # 连接失败
                error_msg = connect_result.stderr.strip() if connect_result.stderr else "未知错误"
                self.oled.wait_for_button_with_text(
                    self.controller,
                    f"❌ 连接失败\n\n{error_msg[:20]}...\n\n当前WiFi保持不变:\n{current_wifi or '未连接'}\n\n按任意键返回菜单"
                )
                print(f"校园网连接失败: {error_msg}")
                
        except Exception as e:
            self.oled.wait_for_button_with_text(
                self.controller,
                f"❌ 连接出错\n\n{str(e)[:20]}...\n\n按任意键返回菜单"
            )
            print(f"校园网连接出错: {e}")
        finally:
            # 返回主菜单
            self.display_menu()

    def disconnect_campus_wifi(self):
        """断开校园网连接"""
        try:
            current_wifi = self.get_current_wifi()
            
            if current_wifi != 'ShanghaiTech':
                self.oled.wait_for_button_with_text(
                    self.controller,
                    f"未连接到校园网\n\n当前WiFi:\n{current_wifi or '未连接'}\n\n按任意键返回菜单"
                )
                self.display_menu()
                return
            
            # 确认断开
            confirm_text = f"确认断开校园网？\n\n当前连接:\nShanghaiTech\n\n按BT1确认断开\n按BT2返回菜单"
            
            result = self.oled.wait_for_button_with_text(
                self.controller,
                confirm_text,
                font_size=10,
                chars_per_line=18,
                visible_lines=4
            )
            
            if hasattr(self.controller, 'last_button'):
                if self.controller.last_button == 'BTN1':
                    # 断开ShanghaiTech连接
                    self.oled.show_text_oled("正在断开校园网...")
                    
                    disconnect_result = subprocess.run([
                        'sudo', 'nmcli', 'connection', 'down', 'ShanghaiTech'
                    ], check=False, capture_output=True, text=True)
                    
                    time.sleep(2)  # 等待断开完成
                    
                    # 尝试自动重连调试WiFi
                    debug_wifi_ssid = self.wifi_configs['default']['ssid']
                    try:
                        reconnect_result = subprocess.run([
                            'sudo', 'nmcli', 'connection', 'up', debug_wifi_ssid
                        ], check=False, capture_output=True, text=True)
                        
                        time.sleep(2)
                        new_wifi = self.get_current_wifi()
                        
                        if new_wifi == debug_wifi_ssid:
                            self.oled.wait_for_button_with_text(
                                self.controller,
                                f"✅ 断开成功！\n\n已断开校园网\n\n自动重连到:\n{debug_wifi_ssid}\n\n按任意键返回菜单"
                            )
                        else:
                            self.oled.wait_for_button_with_text(
                                self.controller,
                                f"✅ 校园网已断开\n\n⚠️ 自动重连失败\n请手动连接WiFi\n\n按任意键返回菜单"
                            )
                    except Exception:
                        self.oled.wait_for_button_with_text(
                            self.controller,
                            f"✅ 校园网已断开\n\n⚠️ 自动重连出错\n请手动连接WiFi\n\n按任意键返回菜单"
                        )
                else:
                    self.display_menu()
            else:
                self.display_menu()
                
        except Exception as e:
            print(f"断开校园网出错: {e}")
            self.oled.wait_for_button_with_text(
                self.controller,
                f"断开出错\n\n{str(e)[:30]}...\n\n按任意键返回菜单"
            )
            self.display_menu()

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
        elif selected_item == "使用调试wifi":
            self.connect_default_wifi()
        elif selected_item == "使用热点wifi":
            self.connect_hotspot_wifi()
        elif selected_item == "连接校园网":
            self.connect_campus_wifi()
        elif selected_item == "断开校园网":
            self.disconnect_campus_wifi()
        elif selected_item == "查看当前wifi":
            self.show_current_wifi()
        elif selected_item == "系统信息":
            self.show_system_info()
        elif selected_item == "重启设备":
            self.system_reboot()
        elif selected_item == "关闭设备":
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
        """清理资源 - 优化版，避免卡死"""
        print("🧹 开始清理资源...")
        
        try:
            # 1. 清理临时WiFi连接配置
            if hasattr(self, 'temp_connections') and self.temp_connections:
                print("🔧 清理临时WiFi连接...")
                for connection_name in self.temp_connections:
                    try:
                        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', connection_name], 
                                     check=False, capture_output=True)
                        print(f"✅ 已删除临时连接: {connection_name}")
                    except Exception as temp_error:
                        print(f"⚠️ 删除临时连接失败: {connection_name} - {temp_error}")
                self.temp_connections.clear()
            
            # 2. 清理控制器（最重要）
            if hasattr(self, 'controller'):
                try:
                    self.controller.cleanup()
                    print("✅ 控制器已清理")
                except Exception as controller_error:
                    print(f"⚠️ 控制器清理失败: {controller_error}")
            
            # 3. 快速清理OLED（避免卡死）
            if hasattr(self, 'oled'):
                try:
                    # 跳过可能卡死的show_text_oled，直接清理
                    self.oled.clear()
                    print("✅ OLED已清理")
                except Exception as oled_error:
                    print(f"⚠️ OLED清理失败: {oled_error}")
            
            # 4. 快速清理LCD（避免卡死）
            if hasattr(self, 'lcd'):
                try:
                    # 使用简单的黑屏清理
                    from PIL import Image
                    black_image = Image.new('RGB', (320, 240), 'black')
                    self.lcd.show_image(black_image)
                    print("✅ LCD已清理")
                except Exception as lcd_error:
                    print(f"⚠️ LCD清理失败: {lcd_error}")
            
            # 5. 最后清理GPIO
            try:
                GPIO.cleanup()
                print("✅ GPIO已清理")
            except Exception as gpio_error:
                print(f"⚠️ GPIO清理失败: {gpio_error}")
            
            print("✅ 所有资源清理完成")
            
        except Exception as e:
            print(f"❌ 清理过程出错: {e}")
        
        # 强制刷新输出
        sys.stdout.flush()

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
    menu = None
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
        
    except KeyboardInterrupt:
        print("\n🛑 检测到Ctrl+C，正在快速退出...")
        if menu:
            try:
                # 快速清理，避免卡死
                if hasattr(menu, 'controller'):
                    menu.controller.cleanup()
                    print("✅ 控制器已清理")
                GPIO.cleanup()
                print("✅ GPIO已清理")
            except Exception as e:
                print(f"⚠️ 快速清理出错: {e}")
        print("👋 程序已退出")
        import os
        os._exit(0)
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        if menu:
            try:
                # 快速清理
                if hasattr(menu, 'controller'):
                    menu.controller.cleanup()
                GPIO.cleanup()
            except:
                pass
        import os
        os._exit(1)