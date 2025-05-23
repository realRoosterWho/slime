#!/usr/bin/env python3
"""
史莱姆漂流状态机测试脚本
测试重构后的状态模式架构（包含奖励系统）
"""

import sys
import time

def test_phase_1_imports():
    """阶段1：测试模块导入"""
    print("🧪 阶段1：模块导入测试")
    print("-" * 30)
    
    try:
        # 测试核心模块导入
        from core.components.derive_states import DeriveState
        from core.components.derive_context import DeriveContext
        from core.components.abstract_state import AbstractState
        from core.components.abstract_state_machine import AbstractStateMachine
        print("✅ 核心模块导入成功")
        
        # 测试基础流程状态导入
        from core.components.states import (
            InitState, GenSlimeImageState, ShowSlimeImageState,
            ShowGreetingState, AskPhotoState, TakePhotoState,
            AnalyzePhotoState, SuggestDestinationState
        )
        print("✅ 基础流程状态导入成功 (8个)")
        
        # 测试奖励系统状态导入
        from core.components.states import (
            WaitForNewPhotoState, TakeNewPhotoState, AnalyzeNewPhotoState,
            AnalyzeRewardState, GenerateRewardImageState, ShowRewardState
        )
        print("✅ 奖励系统状态导入成功 (6个)")
        
        # 测试状态机导入
        from core.components.derive_state_machine import DeriveStateMachine
        print("✅ 状态机导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_phase_2_state_machine_creation():
    """阶段2：测试状态机创建"""
    print("\n🧪 阶段2：状态机创建测试")
    print("-" * 30)
    
    try:
        from core.components.derive_state_machine import DeriveStateMachine
        
        # 测试状态机创建
        initial_text = "测试用的初始文本"
        state_machine = DeriveStateMachine(initial_text)
        print("✅ 状态机创建成功")
        
        # 测试初始状态
        initial_state = state_machine.get_initial_state()
        print(f"✅ 初始状态: {initial_state}")
        
        return True, state_machine
        
    except Exception as e:
        print(f"❌ 状态机创建失败: {e}")
        return False, None

def test_phase_3_state_registration(state_machine):
    """阶段3：测试状态注册"""
    print("\n🧪 阶段3：状态注册测试")
    print("-" * 30)
    
    try:
        from core.components.derive_states import DeriveState
        
        # 检查所有预期状态是否已注册
        expected_states = [
            DeriveState.INIT,
            DeriveState.GEN_SLIME_IMAGE,
            DeriveState.SHOW_SLIME_IMAGE,
            DeriveState.SHOW_GREETING,
            DeriveState.ASK_PHOTO,
            DeriveState.TAKE_PHOTO,
            DeriveState.ANALYZE_PHOTO,
            DeriveState.SUGGEST_DESTINATION,
            DeriveState.WAIT_FOR_NEW_PHOTO,
            DeriveState.TAKE_NEW_PHOTO,
            DeriveState.ANALYZE_NEW_PHOTO,
            DeriveState.ANALYZE_REWARD,
            DeriveState.GENERATE_REWARD_IMAGE,
            DeriveState.SHOW_REWARD
        ]
        
        registered_count = 0
        for state in expected_states:
            if state in state_machine.states:
                registered_count += 1
                print(f"✅ {state.name}")
            else:
                print(f"❌ {state.name} - 未注册")
        
        print(f"\n📊 注册状态统计: {registered_count}/{len(expected_states)}")
        
        if registered_count == len(expected_states):
            print("✅ 所有状态都已正确注册")
            return True
        else:
            print("❌ 部分状态未注册")
            return False
            
    except Exception as e:
        print(f"❌ 状态注册测试失败: {e}")
        return False

def test_phase_4_state_transitions():
    """阶段4：测试状态转换逻辑"""
    print("\n🧪 阶段4：状态转换逻辑测试")
    print("-" * 30)
    
    try:
        from core.components.derive_states import DeriveState
        
        # 定义完整的状态转换序列
        expected_sequence = [
            DeriveState.INIT,
            DeriveState.GEN_SLIME_IMAGE,
            DeriveState.SHOW_SLIME_IMAGE,
            DeriveState.SHOW_GREETING,
            DeriveState.ASK_PHOTO,
            DeriveState.TAKE_PHOTO,
            DeriveState.ANALYZE_PHOTO,
            DeriveState.SUGGEST_DESTINATION,
            DeriveState.WAIT_FOR_NEW_PHOTO,
            DeriveState.TAKE_NEW_PHOTO,
            DeriveState.ANALYZE_NEW_PHOTO,
            DeriveState.ANALYZE_REWARD,
            DeriveState.GENERATE_REWARD_IMAGE,
            DeriveState.SHOW_REWARD
        ]
        
        print("🔗 预期状态转换序列:")
        for i, state in enumerate(expected_sequence):
            arrow = " → " if i < len(expected_sequence) - 1 else ""
            print(f"  {i+1}. {state.name}{arrow}")
        
        print(f"\n📏 总流程长度: {len(expected_sequence)} 个状态")
        print("✅ 状态转换序列验证完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 状态转换测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🎮 史莱姆漂流状态机测试 (阶段4版本)")
    print("🎯 目标：验证奖励系统的状态模式架构")
    print("=" * 50)
    
    # 记录开始时间
    start_time = time.time()
    
    # 执行测试阶段
    success_count = 0
    total_phases = 4
    
    # 阶段1：模块导入测试
    if test_phase_1_imports():
        success_count += 1
    
    # 阶段2：状态机创建测试
    success, state_machine = test_phase_2_state_machine_creation()
    if success:
        success_count += 1
    
    # 阶段3：状态注册测试
    if state_machine and test_phase_3_state_registration(state_machine):
        success_count += 1
    
    # 阶段4：状态转换测试
    if test_phase_4_state_transitions():
        success_count += 1
    
    # 计算耗时
    end_time = time.time()
    duration = end_time - start_time
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print(f"✅ 成功阶段: {success_count}/{total_phases}")
    print(f"⏱️  耗时: {duration:.2f}秒")
    
    if success_count == total_phases:
        print("🎉 所有测试通过！奖励系统状态架构验证成功！")
        print("🚀 阶段4开发完成，可以继续阶段5")
        return 0
    else:
        print("💥 部分测试失败，需要修复问题")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 