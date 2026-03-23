# modules/streams.py
import os
import cv2
import time
import subprocess
import numpy as np
import threading
from typing import Optional

from . import config as C


class CameraStream:
    def __init__(self, index_or_url: str):
        try:
            device = int(index_or_url)
        except Exception:
            device = index_or_url
        self.cap = cv2.VideoCapture(device)

    def read(self):
        if not self.cap.isOpened():
            return False, None
        return self.cap.read()

    def release(self):
        try:
            self.cap.release()
        except Exception:
            pass


class FileStream:
    def __init__(self, path: str):
        self.cap = cv2.VideoCapture(path)

    def read(self):
        if not self.cap.isOpened():
            return False, None
        return self.cap.read()

    def release(self):
        try:
            self.cap.release()
        except Exception:
            pass


class RTSPStream:
    def __init__(self, url: str):
        self.cap = cv2.VideoCapture(url)

    def read(self):
        if not self.cap.isOpened():
            return False, None
        return self.cap.read()

    def release(self):
        try:
            self.cap.release()
        except Exception:
            pass


class ImageStream:
    def __init__(self, path: str):
        self.path = path
        self._img = None

    def read(self):
        if self._img is None:
            img = cv2.imread(self.path)
            if img is None:
                return False, None
            self._img = img
        time.sleep(0.03)
        return True, self._img.copy()

    def release(self):
        pass


class MPVPipeStream:
    """
    用 mpv.exe 解码，把 rawvideo 通过 stdout 输出；Python 读帧。
    """

    def __init__(self, mpv_exe: str, url: str, w=1280, h=720, fps=15):
        self.w, self.h = int(w), int(h)
        self.fps = int(fps)
        self.frame_bytes = self.w * self.h * 3  # rgb24
        self.url = url
        self.p = None
        self.stderr_buffer = []
        self.stderr_thread = None

        if not os.path.exists(mpv_exe):
            raise FileNotFoundError(f"mpv.exe not found: {mpv_exe}")

        # 先测试 mpv 是否可用
        self._test_mpv(mpv_exe)


        # 注意：scale 参数格式要精确，避免自动纵横比调整
        self.cmd = [
            mpv_exe,
            "--no-config",
            "--profile=low-latency",
            "--no-audio",
            "--msg-level=ffmpeg=error",  # 减少 HEVC 错误刷屏
            f"--vf=scale={self.w}:{self.h}:force_original_aspect_ratio=decrease,pad={self.w}:{self.h}:(ow-iw)/2:(oh-ih)/2,format=rgb24",
            # 从 vo = lavc改为标准的编码输出：
            "--of=rawvideo",
            "--ovc=rawvideo",
            "--ovcopts=format=rgb24",
            "--o=-",
            url,
        ]

        print(f"[MPVPIPE] Starting mpv with command:", flush=True)
        print(f"  {' '.join(self.cmd)}", flush=True)

        # Windows: 避免弹出控制台窗口
        creationflags = 0
        try:
            creationflags = subprocess.CREATE_NO_WINDOW
        except Exception:
            pass

        # 启动进程，先等待一下确保 stderr 有输出
        try:
            self.p = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                bufsize=0,
                creationflags=creationflags,
            )
            print(f"[MPVPIPE] mpv process started, PID={self.p.pid}", flush=True)

            # 等待 0.5 秒看是否立即退出
            time.sleep(0.5)
            rc = self.p.poll()
            if rc is not None:
                # 立即退出了，读取所有 stderr
                err = self.p.stderr.read().decode('utf-8', errors='replace')
                raise RuntimeError(f"mpv exited immediately with code {rc}\nStderr:\n{err}")

        except Exception as e:
            if self.p:
                try:
                    self.p.kill()
                except:
                    pass
            raise RuntimeError(f"Failed to start mpv: {e}")

        # 启动 stderr 读取线程
        self.stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self.stderr_thread.start()

    def _test_mpv(self, mpv_exe: str):
        """测试 mpv 是否可用"""
        try:
            result = subprocess.run(
                [mpv_exe, "--version"],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            version = result.stdout.decode('utf-8', errors='replace')
            print(f"[MPVPIPE] mpv version check:\n{version[:200]}", flush=True)
        except Exception as e:
            raise RuntimeError(f"mpv test failed: {e}")

    def _read_stderr(self):
        """后台线程持续读取 stderr"""
        try:
            while True:
                line = self.p.stderr.readline()
                if not line:
                    break
                try:
                    decoded = line.decode('utf-8', errors='replace').rstrip()
                    self.stderr_buffer.append(decoded)
                    if len(self.stderr_buffer) > 100:
                        self.stderr_buffer.pop(0)
                    # 打印所有日志以便调试
                    print(f"[MPVPIPE] {decoded}", flush=True)
                except Exception:
                    pass
        except Exception as e:
            print(f"[MPVPIPE] stderr thread error: {e}", flush=True)

    def _read_exact(self, n: int) -> Optional[bytes]:
        """从 pipe 精确读 n 字节"""
        buf = bytearray()
        deadline = time.time() + 5.0  # 5 秒超时

        while len(buf) < n:
            if time.time() > deadline:
                print(f"[MPVPIPE] Read timeout, got {len(buf)}/{n} bytes", flush=True)
                return None

            if self.p.poll() is not None:
                chunk = self.p.stdout.read(n - len(buf))
                if chunk:
                    buf.extend(chunk)
                break

            chunk = self.p.stdout.read(n - len(buf))
            if not chunk:
                time.sleep(0.001)
                continue
            buf.extend(chunk)

        if len(buf) != n:
            return None
        return bytes(buf)

    def read(self):
        if self.p is None or self.p.poll() is not None:
            if self.p:
                rc = self.p.poll()
                err_msg = "\n".join(self.stderr_buffer[-30:]) if self.stderr_buffer else "(no stderr)"
                print(f"[MPVPIPE] mpv exited rc={rc}", flush=True)
                print(f"[MPVPIPE] stderr:\n{err_msg}", flush=True)
            return False, None

        raw = self._read_exact(self.frame_bytes)
        if raw is None:
            return False, None

        try:
            rgb = np.frombuffer(raw, np.uint8).reshape(self.h, self.w, 3)
            bgr = rgb[:, :, ::-1].copy()
            return True, bgr
        except Exception as e:
            print(f"[MPVPIPE] Frame reshape error: {e}", flush=True)
            return False, None

    def release(self):
        try:
            if self.p and self.p.poll() is None:
                self.p.terminate()
                self.p.wait(timeout=2)
        except Exception:
            pass
        try:
            if self.p and self.p.poll() is None:
                self.p.kill()
        except Exception:
            pass


def open_source(kind: str, value: str):
    """打开输入源"""
    kind = (kind or "").lower()

    # value 为空时的默认值
    if not value or value.strip() == "":
        if kind == "rtsp":
            value = C.RTSP_URL
        elif kind in ("file", "video"):
            value = C.VIDEO_PATH
        elif kind == "image":
            value = C.IMAGE_PATH
        else:
            value = "0"

    if kind == "camera":
        return CameraStream(value)
    elif kind in ("file", "video"):
        return FileStream(value)
    elif kind == "rtsp":
        return RTSPStream(value)
    elif kind == "image":
        return ImageStream(value)
    elif kind in ("mpv", "rtmp", "flv", "hls", "m3u8", "httpflv", "mpvpipe"):
        return MPVPipeStream(C.MPV_EXE, value, w=C.MPV_PIPE_W, h=C.MPV_PIPE_H, fps=C.MPV_PIPE_FPS)
    else:
        raise ValueError(f"未知的输入源类型: {kind}")