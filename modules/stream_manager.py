"""
视频流共享管理器 - 实现流复用和引用计数
对相同的视频源（相同URL）共享同一个流实例，使用引用计数管理流的生命周期
"""

import threading
from typing import Dict, Tuple, Optional, Any
from datetime import datetime
from .streams import open_source

def get_timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


class StreamManager:
    """
    流管理器 - 实现视频流共享
    
    关键特性：
    1. 流复用：相同源的多个请求共享同一个流实例
    2. 引用计数：追踪每个流的使用者数量
    3. 自动释放：引用计数为0时自动释放资源
    4. 线程安全：使用互斥锁保护共享数据
    """
    
    def __init__(self):
        # key: (kind, value) -> 流的唯一标识符
        # value: {"stream": stream_obj, "ref_count": int, "metadata": dict}
        self._streams: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._lock = threading.RLock()  # 可重入锁，防止死锁
    
    def get_stream(self, kind: str, value: str) -> Tuple[Any, str]:
        """
        获取流 - 如果相同源已存在则复用，否则创建新流
        
        Args:
            kind: 流类型 (camera|file|rtsp|image|mpv|mpvpipe|rtmp|flv|hls|m3u8)
            value: 流值 (URL|路径|设备号)
        
        Returns:
            (stream_obj, stream_key) - 流对象和唯一标识符（用于后续释放）
        """
        key = (kind, value)
        
        with self._lock:
            if key in self._streams:
                # 流已存在，增加引用计数
                self._streams[key]["ref_count"] += 1
                count = self._streams[key]["ref_count"]
                print(f"{get_timestamp()} [StreamMgr] Reusing stream: kind={kind}, value={value[:50]}..., ref_count={count}", 
                      flush=True)
                return self._streams[key]["stream"], key
            else:
                # 创建新流
                try:
                    stream = open_source(kind, value)
                    self._streams[key] = {
                        "stream": stream,
                        "ref_count": 1,
                        "metadata": {
                            "kind": kind,
                            "value": value,
                            "created_at": datetime.now(),
                        }
                    }
                    print(f"{get_timestamp()} [StreamMgr] Created new stream: kind={kind}, value={value[:50]}..., ref_count=1", 
                          flush=True)
                    return stream, key
                except Exception as e:
                    print(f"{get_timestamp()} [StreamMgr] ERROR creating stream: {e}", flush=True)
                    raise
    
    def release_stream(self, stream_key: Tuple[str, str]) -> None:
        """
        释放流 - 减少引用计数，当引用计数为0时自动释放资源
        
        Args:
            stream_key: get_stream() 返回的stream_key
        """
        with self._lock:
            if stream_key not in self._streams:
                print(f"{get_timestamp()} [StreamMgr] WARNING: trying to release unknown stream: {stream_key}", 
                      flush=True)
                return
            
            stream_info = self._streams[stream_key]
            stream_info["ref_count"] -= 1
            count = stream_info["ref_count"]
            
            kind, value = stream_key
            
            if count > 0:
                print(f"{get_timestamp()} [StreamMgr] Released stream reference: kind={kind}, value={value[:50]}..., ref_count={count}", 
                      flush=True)
            else:
                # 引用计数为0，释放资源
                try:
                    stream = stream_info["stream"]
                    if hasattr(stream, 'release'):
                        stream.release()
                    print(f"{get_timestamp()} [StreamMgr] Destroyed stream: kind={kind}, value={value[:50]}...", 
                          flush=True)
                except Exception as e:
                    print(f"{get_timestamp()} [StreamMgr] ERROR releasing stream: {e}", flush=True)
                
                del self._streams[stream_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取流管理器统计信息"""
        with self._lock:
            stats = {
                "total_streams": len(self._streams),
                "total_refs": sum(info["ref_count"] for info in self._streams.values()),
                "streams": []
            }
            for (kind, value), info in self._streams.items():
                stats["streams"].append({
                    "kind": kind,
                    "value": value[:50] + ("..." if len(value) > 50 else ""),
                    "ref_count": info["ref_count"],
                    "created_at": info["metadata"]["created_at"].isoformat()
                })
            return stats
    
    def close_all(self) -> None:
        """关闭所有流（通常在应用关闭时调用）"""
        with self._lock:
            for stream_key in list(self._streams.keys()):
                try:
                    stream_info = self._streams[stream_key]
                    stream = stream_info["stream"]
                    if hasattr(stream, 'release'):
                        stream.release()
                    kind, value = stream_key
                    print(f"{get_timestamp()} [StreamMgr] Force-closed stream: kind={kind}", flush=True)
                except Exception as e:
                    print(f"{get_timestamp()} [StreamMgr] ERROR closing stream: {e}", flush=True)
            
            self._streams.clear()
            print(f"{get_timestamp()} [StreamMgr] All streams closed", flush=True)


# 全局流管理器实例
_stream_manager: Optional[StreamManager] = None


def get_stream_manager() -> StreamManager:
    """获取全局流管理器实例（单例）"""
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = StreamManager()
    return _stream_manager
