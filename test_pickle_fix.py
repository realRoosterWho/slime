#!/usr/bin/env python3
"""
测试Pickle修复是否成功

验证性能优化器现在能够正确处理包含不可序列化对象的参数
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from core.components.performance_optimizer import global_optimizer
    from core.components.derive_context import DeriveContext
    from core.components.derive_utils import DeriveImageUtils
    
    print("📦 成功导入模块")
    
    # 测试创建context（包含不可序列化对象）
    print("🧪 创建DeriveContext...")
    context = DeriveContext("测试文本")
    print("✅ DeriveContext创建成功")
    
    # 测试缓存键生成
    print("🔑 测试缓存键生成...")
    image_utils = DeriveImageUtils()
    
    # 这应该不会再抛出pickle错误
    cache_key = global_optimizer.cache_key(
        "test_function", 
        "test_prompt", 
        "save_key", 
        "image_type", 
        context  # 这个对象包含不可序列化的文件对象
    )
    
    print(f"✅ 缓存键生成成功: {cache_key[:16]}...")
    
    # 测试序列化检查方法
    print("🧪 测试序列化检查...")
    print(f"字符串可序列化: {global_optimizer._is_serializable('test')}")
    print(f"数字可序列化: {global_optimizer._is_serializable(123)}")
    print(f"Context不可序列化: {global_optimizer._is_serializable(context)}")
    
    # 清理
    context.cleanup()
    print("🧹 清理完成")
    
    print("\n🎉 所有测试通过！Pickle错误已修复！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 