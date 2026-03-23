#!/usr/bin/env python3
"""
RK3588 Realtime Detector Launcher
"""
import sys
import os
import traceback
import signal
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 信号处理 - 确保优雅退出
def signal_handler(signum, frame):
    print(f"🛑 收到退出信号 {signum}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    import uvicorn
    from modules.main import app
    import logging
    from pathlib import Path
    
    if __name__ == "__main__":
        # 创建日志目录
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "realtime-detector.log"

        print("="*60)
        print("🚀 Starting RK3588 Realtime Detector")
        print(f"📁 Project Root: {project_root}")
        print(f"🐍 Python: {sys.executable}")
        print(f"📝 Log File: {log_file}")
        print("="*60)
        
        print("🔧 准备启动 uvicorn 服务...")
        print("🔧 绑定地址：http://0.0.0.0:8000") 

        try:
            # 使用简化配置，避免复杂的日志配置导致问题
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=8000,
                log_config=None,  # 关键：禁用默认日志配置
                access_log=False  # 暂时禁用访问日志
            )
            
        except KeyboardInterrupt:
            print("🛑 收到键盘中断，正常退出")
        except Exception as uv_error:
            print(f"❌ uvicorn 启动失败！错误：{str(uv_error)}")
            traceback.print_exc()
            sys.exit(1)

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure all dependencies are installed:")
    print("  source /root/venv/bin/activate")
    print("  pip install -r requirements.txt")
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Runtime Error: {e}")
    traceback.print_exc()
    sys.exit(1)
