# modules/logger.py
import sys, os, time, threading
from modules import config as C
os.makedirs(os.path.dirname(C.LOG_FILE), exist_ok=True)

_lock = threading.Lock()
_last_weekday = None  # 记录上次写入日志的星期几

def _ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def log(msg, level="INFO"):
    if not C.DEBUG and level == "DEBUG":
        return
    line = f"{_ts()} [{level}] {msg}"
    with _lock:
        print(line, flush=True)
        try:
            # 检查是否是新的一周（星期一作为一周的开始）
            current_weekday = time.localtime().tm_wday  # 0表示星期一，6表示星期日
            global _last_weekday
            
            # 如果是新的一周，清空日志文件
            if _last_weekday is None or (current_weekday == 0 and _last_weekday != 0):
                with open(C.LOG_FILE, "w", encoding="utf-8") as f:
                    f.write("# 日志文件 - 新的一周开始\n")
                print(f"{_ts()} [INFO] 日志文件已清空，开始新的一周记录", flush=True)
            
            # 更新上次写入的星期几
            _last_weekday = current_weekday
            
            # 写入日志
            with open(C.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            print(f"{_ts()} [ERROR] 写入日志失败: {e}", flush=True)

def dbg(msg): log(msg, "DEBUG")
def inf(msg): log(msg, "INFO")
def wrn(msg): log(msg, "WARN")
def err(msg): log(msg, "ERROR")

