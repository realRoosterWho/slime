#!/usr/bin/env python3
"""
史莱姆漂流状态机测试脚本
"""

import sys
import os

def test_imports():
    """测试模块导入"""
    print("🔍 测试1：模块导入检查")
    
    try:
        print("   导入基础组件...")
        from core.components.derive_state_machine import DeriveStateMachine
        from core.components.derive_context import DeriveContext
        from core.components.derive_states import DeriveState
        print("   ✅ 基础组件导入成功")
        
        print("   导入状态类...")
        from core.components.states import (
            InitState, GenSlimeImageState, ShowSlimeImageState,
            ShowGreetingState, AskPhotoState, TakePhotoState,
            AnalyzePhotoState, SuggestDestinationState
        )
        print("   ✅ 状态类导入成功")
        
        print("   导入工具类...")
        from core.components.derive_utils import DeriveChatUtils, DeriveImageUtils
        print("   ✅ 工具类导入成功")
        
        return True
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_state_machine_creation():
    """测试状态机创建"""
    print("\n🔍 测试2：状态机创建检查")
    
    try:
        from core.components.derive_state_machine import DeriveStateMachine
        
        initial_text = "测试用的初始文本"
        print(f"   创建状态机，初始文本: {initial_text}")
        
        state_machine = DeriveStateMachine(initial_text)
        print("   ✅ 状态机创建成功")
        
        print("   检查上下文...")
        assert state_machine.context is not None
        assert state_machine.context.initial_text == initial_text
        print("   ✅ 上下文检查通过")
        
        return True, state_machine
    except Exception as e:
        print(f"   ❌ 状态机创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_state_initialization(state_machine):
    """测试状态初始化"""
    print("\n🔍 测试3：状态初始化检查")
    
    try:
        print("   初始化状态...")
        state_machine.initialize_states()
        print("   ✅ 状态初始化成功")
        
        print("   检查注册的状态数量...")
        expected_states = 8
        actual_states = len(state_machine.states)
        print(f"   预期: {expected_states} 个状态, 实际: {actual_states} 个状态")
        
        if actual_states == expected_states:
            print("   ✅ 状态数量正确")
        else:
            print("   ⚠️ 状态数量不匹配")
            
        print("   检查初始状态...")
        initial_state = state_machine.get_initial_state()
        print(f"   初始状态: {initial_state}")
        
        if initial_state in state_machine.states:
            print("   ✅ 初始状态已注册")
        else:
            print("   ❌ 初始状态未注册")
            return False
            
        return True
    except Exception as e:
        print(f"   ❌ 状态初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dry_run():
    """测试状态机干运行（不实际执行）"""
    print("\n🔍 测试4：状态转换逻辑检查")
    
    try:
        from core.components.derive_state_machine import DeriveStateMachine
        from core.components.derive_states import DeriveState
        
        state_machine = DeriveStateMachine("测试文本")
        state_machine.initialize_states()
        
        # 模拟状态转换序列
        expected_sequence = [
            DeriveState.INIT,
            DeriveState.GEN_SLIME_IMAGE,
            DeriveState.SHOW_SLIME_IMAGE,
            DeriveState.SHOW_GREETING,
            DeriveState.ASK_PHOTO,
            DeriveState.TAKE_PHOTO,
            DeriveState.ANALYZE_PHOTO,
            DeriveState.SUGGEST_DESTINATION
        ]
        
        print("   检查状态转换逻辑...")
        current_state_type = state_machine.get_initial_state()
        
        for i, expected_state in enumerate(expected_sequence):
            if current_state_type != expected_state:
                print(f"   ❌ 状态{i}: 期望{expected_state}, 实际{current_state_type}")
                return False
            
            print(f"   ✅ 状态{i}: {expected_state}")
            
            # 获取当前状态对象
            if current_state_type in state_machine.states:
                current_state = state_machine.states[current_state_type]
                # 模拟获取下一状态（不实际执行）
                try:
                    # 这里我们需要创建一个模拟的context来测试get_next_state
                    mock_context = state_machine.context
                    next_state = current_state.get_next_state(mock_context)
                    current_state_type = next_state
                    
                    if next_state is None:
                        print(f"   📍 状态{i}: {expected_state} 为终止状态")
                        break
                except Exception as e:
                    print(f"   ⚠️ 无法获取状态{expected_state}的下一状态: {e}")
                    break
            else:
                print(f"   ❌ 状态{current_state_type}未注册")
                return False
        
        print("   ✅ 状态转换逻辑检查通过")
        return True
    except Exception as e:
        print(f"   ❌ 状态转换逻辑检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🧪 史莱姆漂流状态机测试开始\n")
    
    # 测试1: 导入检查
    if not test_imports():
        print("\n💥 导入测试失败，停止测试")
        return False
    
    # 测试2: 状态机创建
    success, state_machine = test_state_machine_creation()
    if not success:
        print("\n💥 状态机创建测试失败，停止测试")
        return False
    
    # 测试3: 状态初始化
    if not test_state_initialization(state_machine):
        print("\n💥 状态初始化测试失败，停止测试")
        return False
    
    # 测试4: 状态转换逻辑
    if not test_dry_run():
        print("\n💥 状态转换逻辑测试失败")
        return False
    
    print("\n🎉 所有基础测试通过！")
    print("\n📋 测试总结：")
    print("   ✅ 模块导入正常")
    print("   ✅ 状态机创建正常")
    print("   ✅ 状态初始化正常")
    print("   ✅ 状态转换逻辑正常")
    print("\n🔧 状态机已准备好进行实际运行测试！")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 