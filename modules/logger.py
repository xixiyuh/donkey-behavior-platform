# modules/logger.py
import sys, os, time, threading
from modules import config as C
os.makedirs(os.path.dirname(C.LOG_FILE), exist_ok=True)

_lock = threading.Lock()

def _ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def log(msg, level="INFO"):
    if not C.DEBUG and level == "DEBUG":
        return
    line = f"{_ts()} [{level}] {msg}"
    with _lock:
        print(line, flush=True)
        try:
            with open(C.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

def dbg(msg): log(msg, "DEBUG")
def inf(msg): log(msg, "INFO")
def wrn(msg): log(msg, "WARN")
def err(msg): log(msg, "ERROR")

