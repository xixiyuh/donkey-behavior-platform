#!/usr/bin/env python3
"""
RK3588 Realtime Detector Launcher
"""
import signal
import sys
import traceback
from pathlib import Path

from backend.config import settings


project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def signal_handler(signum, frame):
    print(f"Received shutdown signal: {signum}")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


try:
    import uvicorn
    from modules.main import app

    if __name__ == "__main__":
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "realtime-detector.log"

        print("=" * 60)
        print("Starting RK3588 Realtime Detector")
        print(f"Project Root: {project_root}")
        print(f"Python: {sys.executable}")
        print(f"Log File: {log_file}")
        print(f"Server: http://{settings.app_host}:{settings.app_port}")
        print("=" * 60)

        try:
            uvicorn.run(
                app,
                host=settings.app_host,
                port=settings.app_port,
                log_config=None,
                access_log=False,
            )
        except KeyboardInterrupt:
            print("Keyboard interrupt received, exiting")
        except Exception as uv_error:
            print(f"uvicorn startup failed: {uv_error}")
            traceback.print_exc()
            sys.exit(1)

except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure all dependencies are installed:")
    print("  pip install -r requirements.txt")
    traceback.print_exc()
    sys.exit(1)

except Exception as e:
    print(f"Runtime Error: {e}")
    traceback.print_exc()
    sys.exit(1)
