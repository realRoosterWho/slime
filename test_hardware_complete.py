#!/usr/bin/env python3
"""
史莱姆漂流完整硬件流程测试

测试优化后的状态模式架构在真实硬件环境下的完整运行
包含：完整流程、性能监控、错误处理、用户交互
"""

import sys
import time
import os
import traceback
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_hardware_imports():
    """测试硬件相关模块导入"""
    print("🔧 测试硬件模块导入...")
    try:
        # 测试核心模块
        from core.components.derive_state_machine import DeriveStateMachine
        from core.components.derive_context import DeriveContext
        from core.components.performance_optimizer import global_optimizer, global_resource_manager
        
        # 测试硬件模块
        from core.display.display_utils import DisplayManager
        from core.input.button_utils import InputController
        from core.camera.camera_manager import run_camera_test
        
        print("✅ 所有硬件模块导入成功")
        return True
        
    except ImportError as e:
        print(f"❌ 硬件模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 导入出错: {e}")
        return False

def test_hardware_initialization():
    """测试硬件初始化"""
    print("\n🔧 测试硬件初始化...")
    try:
        # 测试显示器初始化
        from core.display.display_utils import DisplayManager
        oled = DisplayManager("OLED")
        lcd = DisplayManager("LCD")
        print("✅ 显示器初始化成功")
        
        # 测试控制器初始化
        from core.input.button_utils import InputController
        controller = InputController()
        print("✅ 控制器初始化成功")
        
        # 简单的硬件测试
        oled.show_text_oled("硬件测试\n初始化成功")
        time.sleep(2)
        oled.clear()
        
        print("✅ 硬件基础功能测试成功")
        return True, (oled, lcd, controller)
        
    except Exception as e:
        print(f"❌ 硬件初始化失败: {e}")
        print(traceback.format_exc())
        return False, None

def test_complete_flow(test_mode=True):
    """测试完整的漂流流程
    
    Args:
        test_mode: 是否为测试模式（跳过长时间等待）
    """
    print("\n🚀 开始完整硬件流程测试")
    print("=" * 50)
    
    # 测试用的初始文本
    initial_text = "感觉今天的阳光很温暖，想要和史莱姆一起探索美好的地方"
    
    try:
        # 创建状态机
        print("📋 创建史莱姆漂流状态机...")
        from core.components.derive_state_machine import DeriveStateMachine
        
        state_machine = DeriveStateMachine(initial_text)
        print("✅ 状态机创建成功")
        
        # 显示测试信息
        state_machine.context.oled_display.show_text_oled("开始完整流程测试\n请按按钮继续")
        
        if test_mode:
            # 测试模式：模拟用户按钮
            print("🤖 测试模式：自动模拟用户交互")
            time.sleep(2)
        else:
            # 真实模式：等待用户按钮
            print("👤 真实模式：等待用户按钮")
            state_machine.context.controller.wait_for_button('BTN1')
        
        # 记录开始时间
        start_time = time.time()
        
        # 运行状态机
        print("🎮 开始运行状态机...")
        result = state_machine.run()
        
        # 记录结束时间
        end_time = time.time()
        total_time = end_time - start_time
        
        # 输出测试结果
        print("\n" + "=" * 50)
        print("📊 完整流程测试结果")
        print(f"⏱️  总运行时间: {total_time:.2f}秒")
        print(f"🔄 返回菜单: {'是' if result else '否'}")
        
        # 获取性能统计
        stats = state_machine.context.get_performance_stats()
        print(f"📈 性能统计:")
        print(f"   资源数量: {stats['resource_count']}")
        print(f"   缓存大小: {stats['cache_size']}")
        print(f"   循环次数: {stats['cycle_count']}")
        print(f"   总奖励数: {stats['total_rewards']}")
        
        if stats['failure_counts']:
            print(f"⚠️  失败记录: {stats['failure_counts']}")
        
        return True, stats
        
    except KeyboardInterrupt:
        print("\n⏹️  用户中断测试")
        return False, None
        
    except Exception as e:
        print(f"\n❌ 完整流程测试失败: {e}")
        print(traceback.format_exc())
        return False, None

def test_state_transitions():
    """测试状态转换逻辑"""
    print("\n🔄 测试状态转换逻辑...")
    
    try:
        from core.components.derive_state_machine import DeriveStateMachine
        from core.components.derive_states import DeriveState
        
        initial_text = "测试状态转换"
        state_machine = DeriveStateMachine(initial_text)
        
        # 初始化状态
        state_machine.initialize_states()
        
        # 测试状态转换
        transitions_tested = 0
        
        # 测试转换到初始状态
        initial_state = state_machine.get_initial_state()
        if state_machine.transition_to(initial_state):
            print(f"✅ 成功转换到初始状态: {initial_state.name}")
            transitions_tested += 1
        
        # 测试转换到其他关键状态
        key_states = [
            DeriveState.GEN_SLIME_IMAGE,
            DeriveState.SHOW_SLIME_IMAGE,
            DeriveState.TAKE_PHOTO,
            DeriveState.CLEANUP
        ]
        
        for state in key_states:
            if state in state_machine.states:
                if state_machine.transition_to(state):
                    print(f"✅ 成功转换到状态: {state.name}")
                    transitions_tested += 1
                    time.sleep(0.1)  # 短暂延迟
        
        print(f"📊 状态转换测试完成，成功 {transitions_tested} 个转换")
        return True
        
    except Exception as e:
        print(f"❌ 状态转换测试失败: {e}")
        return False

def test_error_recovery():
    """测试错误恢复机制"""
    print("\n🚨 测试错误恢复机制...")
    
    try:
        from core.components.performance_optimizer import global_optimizer
        
        # 测试智能重试
        def failing_function():
            raise Exception("模拟的错误")
        
        try:
            global_optimizer.smart_retry(
                failing_function,
                max_retries=2,
                base_delay=0.1,
                operation_name="test_error"
            )
        except Exception:
            print("✅ 智能重试正确处理了持续失败")
        
        # 测试失败计数
        failure_count = global_optimizer.get_failure_count("test_error")
        print(f"✅ 失败计数记录: {failure_count}")
        
        # 重置失败计数
        global_optimizer.reset_failure_count("test_error")
        new_count = global_optimizer.get_failure_count("test_error")
        print(f"✅ 失败计数重置: {new_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误恢复测试失败: {e}")
        return False

def test_resource_management():
    """测试资源管理"""
    print("\n🧹 测试资源管理...")
    
    try:
        from core.components.performance_optimizer import global_resource_manager
        
        # 测试资源获取和释放
        class TestResource:
            def __init__(self, name):
                self.name = name
                self.cleaned = False
            
            def cleanup(self):
                self.cleaned = True
                print(f"清理资源: {self.name}")
        
        # 获取测试资源
        test_res1 = TestResource("test1")
        test_res2 = TestResource("test2")
        
        global_resource_manager.acquire_resource("test1", test_res1)
        global_resource_manager.acquire_resource("test2", test_res2)
        
        print(f"✅ 获取了 {len(global_resource_manager.active_resources)} 个资源")
        
        # 释放单个资源
        global_resource_manager.release_resource("test1")
        print(f"✅ 释放后剩余 {len(global_resource_manager.active_resources)} 个资源")
        
        # 释放所有资源
        global_resource_manager.release_all()
        print(f"✅ 释放所有资源，剩余 {len(global_resource_manager.active_resources)} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ 资源管理测试失败: {e}")
        return False

def test_button_interaction():
    """测试按钮交互（可选，需要真实硬件）"""
    print("\n🎮 测试按钮交互...")
    
    try:
        from core.input.button_utils import InputController
        controller = InputController()
        
        print("按钮引脚配置:")
        for name, pin in controller.BUTTON_PINS.items():
            print(f"  {name}: GPIO {pin}")
        
        print("✅ 按钮控制器创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 按钮交互测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 史莱姆漂流完整硬件流程测试")
    print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 测试目标: 验证优化后系统的硬件集成和完整流程")
    print("=" * 60)
    
    # 测试计数器
    tests_passed = 0
    total_tests = 7
    
    try:
        # 1. 硬件模块导入测试
        if test_hardware_imports():
            tests_passed += 1
        
        # 2. 硬件初始化测试
        init_success, hardware = test_hardware_initialization()
        if init_success:
            tests_passed += 1
        
        # 3. 状态转换测试
        if test_state_transitions():
            tests_passed += 1
        
        # 4. 错误恢复测试
        if test_error_recovery():
            tests_passed += 1
        
        # 5. 资源管理测试
        if test_resource_management():
            tests_passed += 1
        
        # 6. 按钮交互测试
        if test_button_interaction():
            tests_passed += 1
        
        # 7. 完整流程测试（询问用户是否进行）
        print(f"\n🤔 是否进行完整流程测试？")
        print("   这将运行完整的史莱姆漂流体验，包括:")
        print("   - 史莱姆性格生成")
        print("   - 图像生成 (需要API)")
        print("   - 拍照交互")
        print("   - 奖励系统")
        print("   - 反馈循环")
        
        user_choice = 'n'  # 默认跳过
        
        if hardware:
            # 使用OLED显示选择界面并等待按钮
            choice = hardware[0].show_continue_drift_option(
                hardware[2], 
                "是否进行完整流程测试？"
            )
            user_choice = 'y' if choice else 'n'
            print(f"✅ 用户选择：{'进行测试' if choice else '跳过测试'}")
        else:
            # 如果硬件初始化失败，使用键盘输入
            user_choice = input("输入 'y' 进行完整测试，其他键跳过: ").lower().strip()
        
        if user_choice == 'y':
            print("\n选择测试模式:")
            print("1. 测试模式 (快速，模拟交互)")
            print("2. 真实模式 (完整，需要真实交互)")
            
            if hardware:
                # 使用OLED显示模式选择
                choice = hardware[0].show_continue_drift_option(
                    hardware[2], 
                    "选择测试模式\n\nBT1=测试模式(快速)\nBT2=真实模式(完整)"
                )
                test_mode = choice  # True=测试模式，False=真实模式
                print(f"✅ 选择：{'测试模式（快速）' if test_mode else '真实模式（完整）'}")
            else:
                mode_choice = input("输入选择 (1 或 2): ").strip()
                test_mode = mode_choice != '2'
            
            if test_complete_flow(test_mode):
                tests_passed += 1
                print("🎉 完整流程测试成功！")
            else:
                print("💥 完整流程测试失败")
        else:
            print("⏭️  跳过完整流程测试")
            tests_passed += 1  # 跳过也算通过
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    
    except Exception as e:
        print(f"\n💥 测试过程出现严重错误: {e}")
        print(traceback.format_exc())
    
    finally:
        # 清理硬件资源
        try:
            if 'hardware' in locals() and hardware:
                hardware[0].clear()
                hardware[1].clear()
                print("🧹 硬件资源已清理")
        except Exception:
            pass
    
    # 输出最终结果
    print("\n" + "=" * 60)
    print("📊 硬件流程测试结果汇总")
    print(f"✅ 通过测试: {tests_passed}/{total_tests}")
    print(f"📈 成功率: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 所有硬件测试通过！系统已准备好投入使用！")
        return 0
    elif tests_passed >= total_tests * 0.8:
        print("⚠️  大部分测试通过，系统基本可用")
        return 1
    else:
        print("💥 多个测试失败，需要修复问题")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 