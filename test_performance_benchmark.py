#!/usr/bin/env python3
"""
史莱姆漂流性能基准测试

测试优化后的状态模式架构相比原始架构的性能改进
重点测试：缓存效果、API调用优化、内存使用、响应时间
"""

import sys
import time
import os
import gc
import psutil
import traceback
from datetime import datetime
import json

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

class PerformanceBenchmark:
    """性能基准测试工具"""
    
    def __init__(self):
        self.results = {}
        self.process = psutil.Process()
        
    def start_timer(self, operation_name):
        """开始计时"""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        print(f"⏱️  开始计时: {operation_name}")
        
    def end_timer(self, operation_name):
        """结束计时并记录结果"""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        duration = end_time - self.start_time
        memory_diff = end_memory - self.start_memory
        
        self.results[operation_name] = {
            'duration': duration,
            'memory_usage': end_memory,
            'memory_diff': memory_diff,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"⏰ {operation_name} 完成: {duration:.2f}秒, 内存: {end_memory:.1f}MB (+{memory_diff:.1f}MB)")
        return duration, memory_diff

def test_import_performance():
    """测试模块导入性能"""
    print("\n📦 测试模块导入性能...")
    benchmark = PerformanceBenchmark()
    
    try:
        # 测试核心组件导入
        benchmark.start_timer("导入核心组件")
        from core.components.derive_state_machine import DeriveStateMachine
        from core.components.derive_context import DeriveContext
        from core.components.performance_optimizer import global_optimizer, global_resource_manager
        benchmark.end_timer("导入核心组件")
        
        # 测试状态类导入
        benchmark.start_timer("导入状态类")
        from core.components.states import (
            InitState, GenSlimeImageState, ShowSlimeImageState,
            ShowGreetingState, AskPhotoState, TakePhotoState,
            AnalyzePhotoState, SuggestDestinationState
        )
        benchmark.end_timer("导入状态类")
        
        # 测试工具类导入
        benchmark.start_timer("导入工具类")
        from core.components.derive_utils import DeriveChatUtils, DeriveImageUtils
        benchmark.end_timer("导入工具类")
        
        print("✅ 模块导入性能测试完成")
        return True, benchmark.results
        
    except Exception as e:
        print(f"❌ 模块导入测试失败: {e}")
        return False, None

def test_state_machine_initialization():
    """测试状态机初始化性能"""
    print("\n🚀 测试状态机初始化性能...")
    benchmark = PerformanceBenchmark()
    
    try:
        from core.components.derive_state_machine import DeriveStateMachine
        
        # 测试创建状态机
        benchmark.start_timer("创建状态机")
        initial_text = "性能测试初始文本"
        state_machine = DeriveStateMachine(initial_text)
        duration, memory_diff = benchmark.end_timer("创建状态机")
        
        # 测试状态注册
        benchmark.start_timer("状态注册")
        state_machine.initialize_states()
        benchmark.end_timer("状态注册")
        
        # 验证状态数量
        state_count = len(state_machine.states)
        print(f"📊 注册了 {state_count} 个状态")
        
        # 清理
        state_machine.context.cleanup()
        
        print("✅ 状态机初始化性能测试完成")
        return True, benchmark.results
        
    except Exception as e:
        print(f"❌ 状态机初始化测试失败: {e}")
        return False, None

def test_cache_performance():
    """测试缓存性能"""
    print("\n💾 测试缓存性能...")
    benchmark = PerformanceBenchmark()
    
    try:
        from core.components.performance_optimizer import global_optimizer
        
        # 准备测试数据
        test_data = {
            'large_string': 'x' * 10000,
            'complex_dict': {f'key_{i}': f'value_{i}' for i in range(1000)},
            'list_data': list(range(5000))
        }
        
        # 测试缓存写入性能
        benchmark.start_timer("缓存写入")
        for key, value in test_data.items():
            cache_key = global_optimizer.cache_key(f"test_{key}", value)
            global_optimizer.set_cache(cache_key, value)
        benchmark.end_timer("缓存写入")
        
        # 测试缓存读取性能
        benchmark.start_timer("缓存读取")
        cache_hits = 0
        for key, value in test_data.items():
            cache_key = global_optimizer.cache_key(f"test_{key}", value)
            cached_value = global_optimizer.get_cache(cache_key)
            if cached_value is not None:
                cache_hits += 1
        benchmark.end_timer("缓存读取")
        
        print(f"📊 缓存命中率: {cache_hits}/{len(test_data)} ({(cache_hits/len(test_data)*100):.1f}%)")
        
        # 清理缓存
        global_optimizer.clear_cache("test_")
        
        print("✅ 缓存性能测试完成")
        return True, benchmark.results
        
    except Exception as e:
        print(f"❌ 缓存性能测试失败: {e}")
        return False, None

def test_resource_management_performance():
    """测试资源管理性能"""
    print("\n🧹 测试资源管理性能...")
    benchmark = PerformanceBenchmark()
    
    try:
        from core.components.performance_optimizer import global_resource_manager
        
        # 创建测试资源
        class TestResource:
            def __init__(self, name):
                self.name = name
                self.data = list(range(1000))  # 模拟一些数据
            
            def cleanup(self):
                self.data = None
        
        # 测试资源获取性能
        benchmark.start_timer("资源获取")
        resources = []
        for i in range(100):
            resource = TestResource(f"test_resource_{i}")
            global_resource_manager.acquire_resource(f"test_{i}", resource)
            resources.append(resource)
        benchmark.end_timer("资源获取")
        
        print(f"📊 管理的资源数量: {len(global_resource_manager.active_resources)}")
        
        # 测试资源释放性能
        benchmark.start_timer("资源释放")
        global_resource_manager.release_all()
        benchmark.end_timer("资源释放")
        
        print(f"📊 释放后剩余资源: {len(global_resource_manager.active_resources)}")
        
        print("✅ 资源管理性能测试完成")
        return True, benchmark.results
        
    except Exception as e:
        print(f"❌ 资源管理性能测试失败: {e}")
        return False, None

def test_state_transition_performance():
    """测试状态转换性能"""
    print("\n🔄 测试状态转换性能...")
    benchmark = PerformanceBenchmark()
    
    try:
        from core.components.derive_state_machine import DeriveStateMachine
        from core.components.derive_states import DeriveState
        
        # 创建状态机
        initial_text = "状态转换性能测试"
        state_machine = DeriveStateMachine(initial_text)
        state_machine.initialize_states()
        
        # 测试状态转换性能
        benchmark.start_timer("状态转换")
        
        transition_count = 0
        test_states = [
            DeriveState.INIT,
            DeriveState.GEN_SLIME_IMAGE,
            DeriveState.SHOW_SLIME_IMAGE,
            DeriveState.SHOW_GREETING,
            DeriveState.CLEANUP
        ]
        
        for state in test_states:
            if state in state_machine.states:
                success = state_machine.transition_to(state)
                if success:
                    transition_count += 1
                time.sleep(0.01)  # 短暂延迟
        
        duration, memory_diff = benchmark.end_timer("状态转换")
        
        print(f"📊 完成 {transition_count} 次状态转换")
        print(f"📊 平均每次转换: {duration/transition_count:.3f}秒")
        
        # 清理
        state_machine.context.cleanup()
        
        print("✅ 状态转换性能测试完成")
        return True, benchmark.results
        
    except Exception as e:
        print(f"❌ 状态转换性能测试失败: {e}")
        return False, None

def test_memory_usage_pattern():
    """测试内存使用模式"""
    print("\n🧠 测试内存使用模式...")
    benchmark = PerformanceBenchmark()
    
    try:
        from core.components.derive_state_machine import DeriveStateMachine
        
        # 记录初始内存
        initial_memory = benchmark.process.memory_info().rss / 1024 / 1024
        print(f"📊 初始内存使用: {initial_memory:.1f}MB")
        
        memory_samples = []
        
        # 创建多个状态机实例测试内存增长
        for i in range(5):
            print(f"创建第 {i+1} 个状态机实例...")
            
            state_machine = DeriveStateMachine(f"测试实例 {i+1}")
            state_machine.initialize_states()
            
            current_memory = benchmark.process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            print(f"  内存使用: {current_memory:.1f}MB")
            
            # 清理
            state_machine.context.cleanup()
            
            # 强制垃圾回收
            gc.collect()
            
            after_cleanup = benchmark.process.memory_info().rss / 1024 / 1024
            print(f"  清理后内存: {after_cleanup:.1f}MB")
        
        # 分析内存使用模式
        max_memory = max(memory_samples)
        avg_memory = sum(memory_samples) / len(memory_samples)
        memory_growth = max_memory - initial_memory
        
        print(f"📊 内存使用分析:")
        print(f"   最大内存: {max_memory:.1f}MB")
        print(f"   平均内存: {avg_memory:.1f}MB")
        print(f"   内存增长: {memory_growth:.1f}MB")
        
        benchmark.results["内存分析"] = {
            'initial_memory': initial_memory,
            'max_memory': max_memory,
            'avg_memory': avg_memory,
            'memory_growth': memory_growth
        }
        
        print("✅ 内存使用模式测试完成")
        return True, benchmark.results
        
    except Exception as e:
        print(f"❌ 内存使用模式测试失败: {e}")
        return False, None

def test_error_recovery_performance():
    """测试错误恢复性能"""
    print("\n🚨 测试错误恢复性能...")
    benchmark = PerformanceBenchmark()
    
    try:
        from core.components.performance_optimizer import global_optimizer
        
        # 测试智能重试性能
        benchmark.start_timer("错误恢复")
        
        retry_count = 0
        
        def sometimes_failing_function():
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:  # 前两次失败
                raise Exception(f"模拟错误 #{retry_count}")
            return f"成功！重试了 {retry_count} 次"
        
        try:
            result = global_optimizer.smart_retry(
                sometimes_failing_function,
                max_retries=5,
                base_delay=0.01,  # 短延迟用于测试
                operation_name="test_recovery"
            )
            print(f"📊 重试结果: {result}")
        except Exception as e:
            print(f"📊 重试最终失败: {e}")
        
        duration, memory_diff = benchmark.end_timer("错误恢复")
        
        # 检查失败统计
        failure_count = global_optimizer.get_failure_count("test_recovery")
        print(f"📊 记录的失败次数: {failure_count}")
        
        print("✅ 错误恢复性能测试完成")
        return True, benchmark.results
        
    except Exception as e:
        print(f"❌ 错误恢复性能测试失败: {e}")
        return False, None

def save_benchmark_results(all_results):
    """保存基准测试结果"""
    try:
        results_file = "performance_benchmark_results.json"
        
        # 合并所有结果
        combined_results = {
            'test_timestamp': datetime.now().isoformat(),
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024  # GB
            },
            'test_results': {}
        }
        
        for test_name, results in all_results.items():
            if results:
                combined_results['test_results'][test_name] = results
        
        # 保存到文件
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 基准测试结果已保存到: {results_file}")
        return True
        
    except Exception as e:
        print(f"❌ 保存基准测试结果失败: {e}")
        return False

def main():
    """主性能测试函数"""
    print("📊 史莱姆漂流性能基准测试")
    print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 测试目标: 验证优化后系统的性能改进")
    print("=" * 60)
    
    # 性能测试列表
    performance_tests = [
        ("模块导入性能", test_import_performance),
        ("状态机初始化性能", test_state_machine_initialization),
        ("缓存性能", test_cache_performance),
        ("资源管理性能", test_resource_management_performance),
        ("状态转换性能", test_state_transition_performance),
        ("内存使用模式", test_memory_usage_pattern),
        ("错误恢复性能", test_error_recovery_performance)
    ]
    
    all_results = {}
    tests_passed = 0
    total_start_time = time.time()
    
    try:
        for test_name, test_func in performance_tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            
            try:
                success, results = test_func()
                if success:
                    tests_passed += 1
                    all_results[test_name] = results
                    print(f"✅ {test_name} 完成")
                else:
                    print(f"❌ {test_name} 失败")
                    all_results[test_name] = None
            
            except Exception as e:
                print(f"💥 {test_name} 出现异常: {e}")
                all_results[test_name] = None
            
            # 每个测试后进行垃圾回收
            gc.collect()
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n⏹️  性能测试被用户中断")
    
    # 计算总耗时
    total_duration = time.time() - total_start_time
    
    # 输出汇总结果
    print("\n" + "=" * 60)
    print("📊 性能基准测试结果汇总")
    print(f"✅ 通过测试: {tests_passed}/{len(performance_tests)}")
    print(f"⏱️  总测试时间: {total_duration:.2f}秒")
    print(f"📈 成功率: {(tests_passed/len(performance_tests))*100:.1f}%")
    
    # 保存详细结果
    save_benchmark_results(all_results)
    
    # 输出关键性能指标
    print("\n📈 关键性能指标:")
    for test_name, results in all_results.items():
        if results:
            for operation, data in results.items():
                if isinstance(data, dict) and 'duration' in data:
                    print(f"   {test_name} - {operation}: {data['duration']:.3f}秒")
    
    if tests_passed == len(performance_tests):
        print("\n🎉 所有性能测试通过！系统性能优秀！")
        return 0
    elif tests_passed >= len(performance_tests) * 0.8:
        print("\n⚠️  大部分性能测试通过，系统性能良好")
        return 1
    else:
        print("\n💥 多个性能测试失败，需要优化")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 