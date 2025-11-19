# test_env.py
import os
import sys

def check_environment():
    print("🔍 检查环境变量...")
    print("=" * 50)
    
    # 关键环境变量
    key_vars = ['PATH', 'PYTHONPATH', 'CONDA_PREFIX', 'VIRTUAL_ENV']
    
    for var in key_vars:
        value = os.getenv(var, '未设置')
        print(f"{var}: {value}")
    
    # 检查 DLL 搜索路径
    print(f"sys.path: {sys.path[:3]}...")  # 只显示前3个
    
    # 尝试导入 ONNX Runtime
    try:
        import onnxruntime as ort
        print(f"✅ ONNX Runtime 导入成功: {ort.__version__}")
        return True
    except Exception as e:
        print(f"❌ ONNX Runtime 导入失败: {e}")
        return False

if __name__ == "__main__":
    check_environment()