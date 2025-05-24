#!/usr/bin/env python3
"""
测试语音输入模块导入
验证修复后的导入路径是否正确
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_voice_import():
    """测试语音输入模块导入"""
    try:
        print("🧪 测试语音输入模块导入...")
        
        # 测试导入voice_input_utils
        print("1. 测试导入 voice_input_utils...")
        from core.components.voice_input_utils import VoiceInputManager, STT_AVAILABLE
        print("✅ voice_input_utils 导入成功")
        
        # 检查STT可用性
        print(f"2. 语音识别可用性: {STT_AVAILABLE}")
        
        if STT_AVAILABLE:
            print("✅ 语音识别模块导入成功")
            
            # 测试导入SpeechToText类
            print("3. 测试导入 SpeechToText...")
            project_root = os.path.dirname(os.path.abspath(__file__))
            stt_path = os.path.join(project_root, "core", "audio")
            if stt_path not in sys.path:
                sys.path.append(stt_path)
            
            from stt_utils import SpeechToText
            print("✅ SpeechToText 类导入成功")
            
            # 检查Google Cloud凭证
            credentials_path = "/home/roosterwho/keys/nth-passage-458018-v2-d7658cf7d449.json"
            if os.path.exists(credentials_path):
                print("✅ Google Cloud凭证文件存在")
            else:
                print("⚠️ Google Cloud凭证文件不存在")
                print(f"   期望路径: {credentials_path}")
                print("   这可能导致语音识别无法工作")
            
        else:
            print("❌ 语音识别模块导入失败")
        
        return STT_AVAILABLE
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("🔧 语音输入模块导入测试")
    print("=" * 50)
    
    success = test_voice_import()
    
    if success:
        print("\n🎉 语音模块导入成功！")
        print("现在可以使用语音输入功能")
        return 0
    else:
        print("\n❌ 语音模块导入失败")
        print("可能需要检查依赖或凭证配置")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 