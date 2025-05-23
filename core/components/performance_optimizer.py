"""
史莱姆漂流性能优化工具

该模块提供统一的性能优化策略：
- API调用缓存和去重
- 智能重试机制
- 资源管理
- 错误恢复
"""

import time
import hashlib
import pickle
import os
from typing import Dict, Any, Optional, Callable, Tuple
from functools import wraps

class PerformanceOptimizer:
    """性能优化器，提供缓存、重试、去重等功能"""
    
    def __init__(self, cache_dir: str = None, enable_cache: bool = True):
        self.enable_cache = enable_cache
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), '.derive_cache')
        self.memory_cache = {}  # 内存缓存
        self.api_call_times = {}  # API调用时间记录
        self.failure_counts = {}  # 失败计数器
        
        # 创建缓存目录
        if self.enable_cache and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def cache_key(self, func_name: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 将参数序列化并生成哈希
        cache_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        cache_str = pickle.dumps(cache_data, protocol=pickle.HIGHEST_PROTOCOL)
        return hashlib.md5(cache_str).hexdigest()
    
    def get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.enable_cache:
            return None
        
        # 先检查内存缓存
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # 检查磁盘缓存
        cache_file = os.path.join(self.cache_dir, f"{key}.cache")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    # 同时存入内存缓存
                    self.memory_cache[key] = data
                    return data
            except Exception:
                # 缓存文件损坏，删除它
                os.remove(cache_file)
        
        return None
    
    def set_cache(self, key: str, value: Any) -> None:
        """设置缓存"""
        if not self.enable_cache:
            return
        
        # 存入内存缓存
        self.memory_cache[key] = value
        
        # 存入磁盘缓存
        cache_file = os.path.join(self.cache_dir, f"{key}.cache")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception:
            # 缓存写入失败，忽略
            pass
    
    def is_api_rate_limited(self, api_name: str, min_interval: float = 1.0) -> bool:
        """检查API是否被频率限制"""
        current_time = time.time()
        last_call_time = self.api_call_times.get(api_name, 0)
        
        if current_time - last_call_time < min_interval:
            return True
        
        return False
    
    def record_api_call(self, api_name: str) -> None:
        """记录API调用时间"""
        self.api_call_times[api_name] = time.time()
    
    def get_failure_count(self, operation: str) -> int:
        """获取操作失败次数"""
        return self.failure_counts.get(operation, 0)
    
    def record_failure(self, operation: str) -> None:
        """记录操作失败"""
        self.failure_counts[operation] = self.failure_counts.get(operation, 0) + 1
    
    def reset_failure_count(self, operation: str) -> None:
        """重置操作失败计数"""
        self.failure_counts[operation] = 0
    
    def smart_retry(self, 
                   func: Callable, 
                   max_retries: int = 3, 
                   base_delay: float = 1.0,
                   exponential_backoff: bool = True,
                   retry_on_exceptions: Tuple = (Exception,),
                   operation_name: str = None) -> Any:
        """智能重试机制
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            base_delay: 基础延迟时间
            exponential_backoff: 是否使用指数退避
            retry_on_exceptions: 需要重试的异常类型
            operation_name: 操作名称，用于失败统计
        """
        operation = operation_name or func.__name__
        
        for attempt in range(max_retries + 1):
            try:
                result = func()
                # 成功则重置失败计数
                self.reset_failure_count(operation)
                return result
                
            except retry_on_exceptions as e:
                self.record_failure(operation)
                
                if attempt == max_retries:
                    # 最后一次尝试失败
                    print(f"❌ {operation} 重试 {max_retries} 次后仍然失败: {str(e)}")
                    raise
                
                # 计算延迟时间
                if exponential_backoff:
                    delay = base_delay * (2 ** attempt)
                else:
                    delay = base_delay
                
                print(f"⚠️  {operation} 第 {attempt + 1} 次尝试失败: {str(e)}")
                print(f"🔄 等待 {delay:.1f} 秒后重试...")
                
                time.sleep(delay)
    
    def clear_cache(self, pattern: str = None) -> None:
        """清理缓存"""
        # 清理内存缓存
        if pattern:
            keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.memory_cache[key]
        else:
            self.memory_cache.clear()
        
        # 清理磁盘缓存
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    if not pattern or pattern in filename:
                        try:
                            os.remove(os.path.join(self.cache_dir, filename))
                        except Exception:
                            pass

def cached_api_call(optimizer: PerformanceOptimizer, 
                   api_name: str, 
                   cache_duration: int = 300,  # 5分钟缓存
                   rate_limit: float = 1.0):
    """API调用缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = optimizer.cache_key(api_name, *args, **kwargs)
            
            # 检查缓存
            cached_result = optimizer.get_cache(cache_key)
            if cached_result is not None:
                print(f"🎯 使用缓存结果: {api_name}")
                return cached_result
            
            # 检查频率限制
            if optimizer.is_api_rate_limited(api_name, rate_limit):
                wait_time = rate_limit - (time.time() - optimizer.api_call_times.get(api_name, 0))
                print(f"⏳ API频率限制，等待 {wait_time:.1f} 秒...")
                time.sleep(wait_time)
            
            # 执行API调用
            def api_call():
                optimizer.record_api_call(api_name)
                return func(*args, **kwargs)
            
            # 使用智能重试
            result = optimizer.smart_retry(
                api_call,
                max_retries=3,
                operation_name=f"api_{api_name}"
            )
            
            # 缓存结果
            optimizer.set_cache(cache_key, result)
            
            return result
        
        return wrapper
    return decorator

class ResourceManager:
    """资源管理器，确保资源的正确分配和释放"""
    
    def __init__(self):
        self.active_resources = {}  # 活跃资源
        self.resource_locks = {}    # 资源锁
    
    def acquire_resource(self, resource_name: str, resource_obj: Any) -> None:
        """获取资源"""
        if resource_name in self.active_resources:
            print(f"⚠️  资源 {resource_name} 已存在，将被替换")
            self.release_resource(resource_name)
        
        self.active_resources[resource_name] = resource_obj
        print(f"📌 获取资源: {resource_name}")
    
    def release_resource(self, resource_name: str) -> None:
        """释放资源"""
        if resource_name in self.active_resources:
            resource = self.active_resources[resource_name]
            
            # 尝试调用资源的清理方法
            cleanup_methods = ['cleanup', 'close', 'dispose', 'clear']
            for method_name in cleanup_methods:
                if hasattr(resource, method_name):
                    try:
                        getattr(resource, method_name)()
                        print(f"🧹 释放资源: {resource_name} (调用 {method_name})")
                        break
                    except Exception as e:
                        print(f"⚠️  释放资源 {resource_name} 时出错: {e}")
            
            del self.active_resources[resource_name]
    
    def release_all(self) -> None:
        """释放所有资源"""
        for resource_name in list(self.active_resources.keys()):
            self.release_resource(resource_name)
    
    def get_resource_status(self) -> Dict[str, str]:
        """获取资源状态"""
        status = {}
        for name, resource in self.active_resources.items():
            status[name] = f"{type(resource).__name__} - {id(resource)}"
        return status

# 全局性能优化器实例
global_optimizer = PerformanceOptimizer()
global_resource_manager = ResourceManager() 