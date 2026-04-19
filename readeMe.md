# RK3588 实时检测系统

基于 FastAPI + WebSocket + YOLO 的实时视频流检测系统，支持多种视频源（RTSP、HLS、本地文件等），可部署在 RK3588 开发板或 Windows/Linux 环境。

powerShell:
& "D:\Anaconda3\shell\condabin\conda-hook.ps1"
conda activate E:\Anaconda3\envs\donkey_track

cmd:
conda activate donkey_track
e:
cd E:\donkey\萤石云\realtime-detector
uvicorn modules.main:app --host 127.0.0.1 --port 8080
http://127.0.0.1:8080/

conda activate donkey_track
e:
cd E:\donkey\萤石云\realtime-detector\vue-frontend
npm run dev
http://localhost:5173/detection
查看接口：
http://127.0.0.1:8080/session-stats

https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_1_2.flv?expire=1799307668&id=930848885333229568&t=3d7f5c7af02f666391f092204cae900f60e075481b289e74400314063d7f0085&ev=101&supportH265=1
https://open.ys7.com/v3/openlive/FR3098735_1_2.m3u8?expire=1799307668&id=930848885066555392&t=acfcf2b5652add9dfa2239bd5b386ae5b808aace4dad6c0aac1a0168448b4113&ev=101&supportH265=1

https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_16_2.flv?expire=1799376370&id=931137041373081600&t=4d1ff7477c74c407a64011907deb7cb38b612dfe2ec0a2fac020ae851c409a29&ev=101&supportH265=1
https://open.ys7.com/v3/openlive/FR3098735_16_2.m3u8?expire=1799376370&id=931137041116553216&t=00e8fed619c30d183ab8166f74af8cf036a6f06f564311714b748034fcb90979&ev=101&supportH265=1
---

## 📋 目录结构

```
realtime-detector/
├── modules/
│   ├── config.py           # 全局配置（模型路径、阈值、流参数等）
│   ├── main.py             # FastAPI 主服务 + WebSocket 端点
│   ├── detector_pt.py      # PyTorch YOLO 检测器（Windows/开发阶段）
│   ├── detector_rknn.py    # RKNN Lite YOLO 检测器（RK3588 部署）
│   ├── streams.py          # 多种视频流源封装
│   ├── websocket_manager.py # WebSocket 连接管理 + 帧率控制
│   ├── overlays.py         # 绘制检测框和 FPS 显示
│   ├── postprocess.py      # RKNN 后处理（NMS、letterbox 还原等）
│   └── logger.py           # 日志模块
├── models/                 # 模型文件目录
│   └── 0710-best-YOLO.pt   # YOLO 权重文件
├── static/
│   └── index.html          # Web 前端界面
├── data/                   # 测试数据
│   ├── demo.mp4
│   └── 111.png
└── run.py                  # 启动脚本
```

---

## 🔧 核心模块详解

### 1. `config.py` - 全局配置中心

```python
# 模型配置
IMG_SIZE = (640, 640)       # 输入尺寸 (宽, 高)
CLASSES = ("standing", "mating", "lying")  # 检测类别
CONF_THRES = 0.25           # 置信度阈值
IOU_THRES = 0.45            # NMS IoU 阈值

# 性能优化
MAX_FPS = 20                # WebSocket 最大推送帧率
FRAME_INTERVAL = 1          # 每 N 帧推理一次（1=每帧都推理）
JPEG_QUALITY = 80           # WebSocket 传输 JPEG 质量
QUEUE_MAX = 2               # 队列最大长度（低延迟模式）

# MPV 流配置
MPV_EXE = r"D:\mpv\...\mpv.exe"
MPV_PIPE_W = 1280           # MPV 输出宽度
MPV_PIPE_H = 720            # MPV 输出高度
MPV_PIPE_FPS = 15           # MPV 输出帧率
```

**⚠️ 重要配置项**：
- `PT_MODEL_PATH`：Windows 环境使用 `.pt` 模型
- `YOLO_MODEL_PATH`：RK3588 环境使用 `.rknn` 模型
- `FRAME_INTERVAL`：设为 2-3 可提升性能，但会降低检测频率
- `QUEUE_MAX = 2`：保持低延迟，牺牲部分帧

---

### 2. `main.py` - FastAPI 主服务

#### 核心流程

```python
# 1. 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：预加载模型 + 预热
    det = get_detector()
    det.infer_once(dummy_frame)  # 预热避免首帧延迟
    
    yield
    
    # 关闭时：释放资源
    detector.release()

# 2. WebSocket 端点
@app.websocket("/ws")
async def ws_endpoint(ws, kind, value):
    # 打开视频流
    stream = open_source(kind, value)
    
    # 启动双线程流水线
    start_pipeline(stream, detector, result_queue, stop_event)
    
    # 推送检测结果
    while True:
        frame = result_queue.get()
        await ws_manager.send_frame(ws, frame)
```

#### 双线程流水线架构

```python
def start_pipeline(stream, det, result_queue, stop_event):
    # 线程 1: Reader（持续读取帧）
    def reader():
        while not stop_event.is_set():
            ok, frame = stream.read()
            
            # 低延迟策略：清空旧帧，只保留最新
            while not frame_queue.empty():
                frame_queue.get_nowait()
            
            frame_queue.put(frame, timeout=0.01)
    
    # 线程 2: Infer（推理 + 绘制）
    def infer():
        while not stop_event.is_set():
            frame = frame_queue.get(timeout=0.1)
            
            # 跳帧推理（根据 FRAME_INTERVAL）
            if idx % FRAME_INTERVAL == 0:
                r, dt = det.infer_once(frame)
                frame = det.annotate(frame, r)
            
            put_fps(frame, last_fps)
            
            # 同样策略：只保留最新结果
            result_queue.put(frame)
```

**🎯 设计亮点**：
- **双队列解耦**：读取和推理独立，避免阻塞
- **帧丢弃策略**：优先保证实时性，牺牲完整性
- **异常隔离**：推理错误不影响流读取

---

### 3. `streams.py` - 多源视频流封装

支持 7 种视频源：

| 类型 | 类名 | 适用场景 | 示例 |
|------|------|----------|------|
| `camera` | `CameraStream` | USB 摄像头 | `kind=camera&value=0` |
| `file` | `FileStream` | 本地视频 | `kind=file&value=/path/to/video.mp4` |
| `rtsp` | `RTSPStream` | RTSP 流 | `kind=rtsp&value=rtsp://...` |
| `image` | `ImageStream` | 静态图片 | `kind=image&value=/path/to/img.jpg` |
| `mpv` | `MPVPipeStream` | HLS/HTTP-FLV/RTMP | `kind=mpv&value=https://...m3u8` |

#### MPVPipeStream 实现细节

```python
class MPVPipeStream:
    def __init__(self, mpv_exe, url, w=1280, h=720, fps=15):
        # MPV 命令行参数
        self.cmd = [
            mpv_exe,
            "--profile=low-latency",      # 低延迟模式
            "--no-audio",                  # 禁用音频
            "--msg-level=ffmpeg=error",    # 减少日志
            
            # 关键滤镜链：缩放 + 填充 + 格式转换
            f"--vf=scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,format=rgb24",
            
            # 原始视频输出到 stdout
            "--of=rawvideo",
            "--ovc=rawvideo",
            "--o=-",
            url,
        ]
        
        # 启动进程
        self.p = subprocess.Popen(self.cmd, stdout=PIPE, stderr=PIPE)
        
        # 后台线程读取 stderr（避免管道阻塞）
        threading.Thread(target=self._read_stderr, daemon=True).start()
    
    def read(self):
        # 精确读取一帧字节数
        raw = self._read_exact(self.w * self.h * 3)
        
        # 解析为 NumPy 数组
        rgb = np.frombuffer(raw, np.uint8).reshape(self.h, self.w, 3)
        bgr = rgb[:, :, ::-1].copy()  # RGB → BGR
        return True, bgr
```

**⚠️ MPV 使用注意事项**：
1. **必须安装 mpv.exe**：下载地址 https://mpv.io/installation/
2. **stderr 必须异步读取**：否则管道满会导致 mpv 挂起
3. **滤镜顺序很重要**：
   ```
   scale (缩放) → pad (填充) → format (格式转换)
   ```
4. **固定输出尺寸**：`MPV_PIPE_W × MPV_PIPE_H` 必须固定，否则无法按字节流切帧

---

### 4. `detector_pt.py` vs `detector_rknn.py`

#### PyTorch 版本（开发/Windows）

```python
class PTDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)  # Ultralytics YOLO
    
    def infer_once(self, frame_bgr):
        r = self.model.predict(frame_bgr, verbose=False)[0]
        return r, dt
    
    def annotate(self, frame, r):
        return r.plot()  # 内置画框功能
```

#### RKNN 版本（RK3588 部署）

```python
class RKNNDetector:
    def __init__(self):
        self.rknn = RKNNLite()
        self.rknn.load_rknn(C.YOLO_MODEL_PATH)
        self.rknn.init_runtime(core_mask=C.RKNN_CORE_MASK)
    
    def infer_once(self, frame):
        # 1. 预处理：letterbox + BGR→RGB
        img, info = self.preprocess(frame)
        
        # 2. 推理（输入必须是 NHWC uint8）
        outputs = self.rknn.inference(inputs=[img[np.newaxis, ...]])
        
        # 3. 后处理：decode + NMS + 还原坐标
        dets = decode_yolo_rknn(outputs, info)
        return dets, dt
    
    def annotate(self, frame, dets):
        return draw_detections(frame, dets)
```

**🔑 关键差异**：
- **输入格式**：RKNN 需要 `NHWC uint8`，PyTorch 接受 `HWC BGR`
- **后处理**：RKNN 需要手动实现 NMS（`postprocess.py`）
- **坐标还原**：RKNN 需要根据 letterbox 参数还原（`unletter_box_xyxy`）

---

### 5. `postprocess.py` - RKNN 后处理流程

```python
def decode_yolo_rknn(outputs, letter_info):
    """
    完整的 YOLO 后处理流程
    
    输入:
        outputs: List[np.ndarray]  # RKNN 推理输出
        letter_info: LetterBoxInfo # letterbox 变换参数
    
    输出:
        dets: np.ndarray [N, 6]    # [x1, y1, x2, y2, score, class_id]
    """
    
    # 1. 解析多尺度输出 (3 个检测头)
    boxes, classes, scores = post_process(outputs)
    
    # 2. 坐标还原到原图
    boxes = unletter_box_xyxy(boxes, letter_info)
    
    # 3. 拼接结果
    return np.concatenate([boxes, scores, class_ids], axis=1)
```

#### DFL (Distribution Focal Loss) 解码

```python
def dfl(position: np.ndarray) -> np.ndarray:
    """
    将分布式边界框预测转换为精确坐标
    
    输入: [n, 4*mc, h, w]  # mc 是分布宽度（通常为 16）
    输出: [n, 4, h, w]     # 4 个边界的期望值
    """
    n, c, h, w = position.shape
    mc = c // 4
    
    # Reshape → [n, 4, mc, h, w]
    y = position.reshape(n, 4, mc, h, w)
    
    # Softmax + 加权求和
    y = softmax(y, axis=2)
    acc = np.arange(mc).reshape(1, 1, mc, 1, 1)
    y = (y * acc).sum(axis=2)
    
    return y  # [n, 4, h, w]
```

**📊 后处理性能优化**：
- 全 NumPy 实现，无 PyTorch 依赖
- NMS 使用向量化操作
- letterbox 还原避免循环

---

### 6. `websocket_manager.py` - 帧率控制

```python
class WSManager:
    def __init__(self, max_fps=20):
        self.interval = 1.0 / max_fps
        self._last = 0
    
    async def send_frame(self, ws, frame):
        # 帧率限制
        now = time.time()
        if now - self._last < self.interval:
            await asyncio.sleep(self.interval - (now - self._last))
        self._last = time.time()
        
        # JPEG 编码 + Base64
        ok, buffer = cv2.imencode('.jpg', frame, 
                                  [cv2.IMWRITE_JPEG_QUALITY, C.JPEG_QUALITY])
        frame_data = base64.b64encode(buffer).decode('utf-8')
        
        await ws.send_text(frame_data)
```

**⚡ 带宽优化**：
- `MAX_FPS = 20`：限制最大推送频率
- `JPEG_QUALITY = 80`：平衡画质和带宽
- 动态丢帧：推送慢于生产时自动跳过中间帧

---

## 🎯 视频流共享架构（SourceSessionManager）

### 核心设计理念

**从每连接独立Pipeline → 同源共享Pipeline**

#### 问题背景

```
传统方式（每连接独立）：
    摄像头A
    ├─ 后台检测 → reader线程1 + infer线程1
    ├─ 用户1 → reader线程2 + infer线程2
    ├─ 用户2 → reader线程3 + infer线程3
    └─ 用户3 → reader线程4 + infer线程4
    
结果：8个线程，推理4次，内存占用4倍，CPU占用4倍 ❌

新架构（同源共享）：
    摄像头A
    └─ SourceSession → reader线程(共享) + infer线程(共享)
        ├─ 后台检测（虚拟订阅者）
        ├─ 用户1 WebSocket（订阅者）
        ├─ 用户2 WebSocket（订阅者）
        └─ 用户3 WebSocket（订阅者）
    
结果：2个线程，推理1次，内存占用1倍，CPU占用1倍 ✅
```

---

### 1. Session状态机

每个 `SourceSession` 都有明确的状态转移：

```
┌──────────┐
│ starting │  ← 初始化 reader 和 infer 线程
└────┬─────┘
     │ 成功启动
     ↓
┌──────────┐
│ running  │  ← 正常读取和推理
└────┬─────┘
     │ 1. 丢帧/连接失败
     │ 2. is_within_time_range() = false
     ↓
┌──────────────┐
│ reconnecting │  ← 执行双阶段重连
└────┬─────────┘
     │ 1. 重连成功 → 返回 running
     │ 2. 重连失败 → 进入 error
     │ 3. stop_event.is_set() → 进入 stopped
     ↓
┌──────────┐
│  error   │  ← 重连彻底失败或异常
└────┬─────┘
     │ 手动停止或TTL释放
     ↓
┌──────────┐
│ stopped  │  ← 资源已释放
└──────────┘
```

**状态定义**：

| 状态 | 含义 | reader活跃 | infer活跃 | 可播放 |
|------|------|----------|----------|--------|
| `starting` | 正在启动线程 | ⏳ | ⏳ | ❌ |
| `running` | 正常运行 | ✅ | ✅ | ✅ |
| `reconnecting` | 重连中（第一阶段或第二阶段） | ⏳ | ⏳ | ❌ 卡住 |
| `idle` | 无订阅者且超时 | ❌ | ❌ | ❌ |
| `error` | 重连失败/异常 | ❌ | ❌ | ❌ |
| `stopped` | 已停止 | ❌ | ❌ | ❌ |

前端可以通过 `/session-stats` 接口获取当前状态，实现UI反馈。

---

### 2. 增强的统计接口 `/session-stats`

#### 返回结构

```json
{
  "status": "ok",
  "timestamp": "2026-04-19T16:30:00",
  "sessions": {
    "total_sessions": 2,
    "total_subscribers": 5,
    "sessions": [
      {
        "source_key": "flv:https://rtmp.example.com/stream.flv@camera3",
        "session_id": 140001,
        "stream_id": 220001,
        "detector_id": 330001,
        "state": "running",
        "kind": "flv",
        "value": "https://rtmp.example.com/stream.flv",
        "camera_id": "camera3",
        "ref_count": 3,
        "subscriber_count": 3,
        "task_holders_count": 1,
        "ws_subscribers_count": 2,
        "reader_alive": true,
        "infer_alive": true,
        "infer_count": 487,
        "start_count": 1,
        "frame_no": 156,
        "last_frame_time": "2026-04-19T16:30:00.123",
        "last_infer_time": "2026-04-19T16:30:00.456",
        "created_at": "2026-04-19T16:25:00",
        "last_active_time": "2026-04-19T16:30:00"
      }
    ]
  }
}
```

#### 字段详解

| 字段 | 含义 | 用途 |
|------|------|------|
| `state` | 当前状态（starting/running/reconnecting/idle/error/stopped） | 前端展示状态指示器 |
| `kind` | 视频源类型（flv/rtsp/mpv等） | 调试源类型问题 |
| `value` | 视频源URL（已归一化） | 排查URL错误 |
| `camera_id` | 摄像头ID | 区分同一type的不同源 |
| `ref_count` | 总订阅引用计数 | 监控session生命周期 |
| `subscriber_count` | 当前订阅者数量 | 实时查看有多少人在用 |
| `task_holders_count` | 后台检测虚拟订阅者数 | 区分后台任务与前端用户 |
| `ws_subscribers_count` | 实际WebSocket订阅者数 | 前端实时用户数 |
| `reader_alive` | reader线程是否活跃 | 判断流读取是否正常 |
| `infer_alive` | infer线程是否活跃 | 判断推理是否正常 |
| `infer_count` | 累计推理次数 | 性能统计 |
| `start_count` | pipeline启动次数 | 检测是否频繁重启 |
| `frame_no` | 当前帧编号 | 检测是否停止推进 |
| `last_frame_time` | 最后一帧时间 | 检测是否卡住 |
| `last_infer_time` | 最后推理时间 | 检测推理是否进行 |

---

### 3. 两条链路详解

#### 链路1：后台定时检测（CameraDetectionManager）

```
API: POST /camera-configs
   ↓
CameraDetectionManager.start_detection(camera_config)
   ↓
创建 detection_thread（daemon=True）
   ↓
生成 SourceKey：
   kind='flv'
   value=camera_config['flv_url']
   camera_id=camera_config['camera_id']
   ↓
try_reconnect()
   ├─ 第一阶段：10秒×4次 (40秒)
   └─ 第二阶段：等待1小时 + 10秒×3次
   ↓
session_mgr.get_or_create_session(source_key, stream, detector)
   ↓
session.add_subscriber("scheduled_task_{config_id}")  ← 虚拟订阅者
   ↓
while not stop_event.is_set():
   ├─ 每5分钟检查 is_within_time_range()
   ├─ 监控 session.get_latest_result() 是否有效
   └─ 丢帧时触发 try_reconnect()
   ↓
finally:
   session.remove_subscriber()
   清理资源
```

**特点**：
- ✅ **虚拟订阅者**：不是WebSocket，只是字符串标记
- ✅ **工作时间约束**：配置时间外不拉流
- ✅ **双阶段自动重连**：连接失败时自动恢复
- ✅ **持续监控**：丢帧自动重连

#### 链路2：实时监看（WebSocket /ws）

```
Frontend: ws://host:port/ws?kind=flv&value=URL&camera_id=xxx
   ↓
ws_endpoint()
   ↓
生成 SourceKey：
   kind=Query(kind)
   value=urldecode(Query(value))  ← 关键：前端URL编码，服务端必须解码
   camera_id=Query(camera_id)
   ↓
session_mgr.get_or_create_session(source_key, stream, detector)
   ↓
session.add_subscriber(ws)  ← 真实WebSocket订阅者
   ↓
while True:
   ├─ frame = session.get_latest_result()
   ├─ [BROADCAST] 日志（每10帧）
   ├─ await ws_manager.send_frame(ws, frame)
   └─ [SEND] 日志（每10帧）
   ↓
finally:
   session.remove_subscriber(ws)
   清理资源
```

**特点**：
- ✅ **真实订阅者**：WebSocket连接对象
- ✅ **按需连接**：用户打开页面才连接
- ✅ **自动清理**：断开时自动释放
- ❌ **无时间约束**：随时可连接
- ❌ **无自动重连**：连接失败就断开

---

### 4. 多订阅者场景示例

#### 场景A：只有后台检测

```
session_id=140001
├─ ref_count=1
│  └─ "scheduled_task_7" (后台检测)
├─ reader_alive=✅
├─ infer_alive=✅
├─ state=running
└─ 推理结果只在内存中循环，没人消费
```

日志示例：
```
[SESSION-CREATE] source_key=flv:https://...@camera3 session_id=140001
[PIPELINE-START] source_key=... start_count=1
[INFER] source_key=... infer_count=100 subscriber_count=1
```

#### 场景B：后台检测 + 1个WebSocket用户

```
session_id=140001
├─ ref_count=2
│  ├─ "scheduled_task_7" (后台检测)
│  └─ ws_obj_1 (用户A)
├─ reader_alive=✅ (只有1个！)
├─ infer_alive=✅ (只有1个！)
├─ state=running
└─ 推理结果被广播给两个订阅者
   ├─ 用户A接收JPEG → 前端显示
   └─ 后台检测隐式获得结果
```

日志示例：
```
[SESSION-REUSE] source_key=... session_id=140001
[INFER] source_key=... infer_count=100 subscriber_count=2
[BROADCAST] source_key=... subscriber_count=2
[SEND] source_key=... ws_id=XXXXX
```

#### 场景C：后台检测 + 3个WebSocket用户

```
session_id=140001
├─ ref_count=4
│  ├─ "scheduled_task_7" (后台检测)
│  ├─ ws_obj_1 (用户A)
│  ├─ ws_obj_2 (用户B)
│  └─ ws_obj_3 (用户C)
├─ reader_alive=✅ (只有1个！)
├─ infer_alive=✅ (只有1个！)
├─ state=running
├─ infer_count=300 (总共推理300次)
└─ reader_fps≈25
```

**对比传统方式**：
| 指标 | 传统方式 | 共享Pipeline |
|------|---------|-------------|
| 线程数 | 8（后台2 + 3用户×2） | 2（共享）|
| 推理次数/秒 | 4次 | 1次 |
| 内存占用 | 4倍 | 1倍 |
| CPU占用 | 4倍 | 1倍 |

---

### 5. 重连与广播状态联动

#### 重连过程中的前端体验

当session进入 `reconnecting` 状态：

```
状态转移：
running ──[丢帧] → reconnecting
   ↓
[RECONNECT] Stage 1 - Attempt 1/4
[RECONNECT] Stage 1 - Attempt 2/4
...
[RECONNECT] Stage 1 exhausted, entering Stage 2
[RECONNECT] Stage 2 - Waiting 60 minutes

前端应该：
❌ 停止播放旧结果（显示"正在重连"提示）
❌ 灰显UI控件
❌ 显示重连倒计时
```

**状态字段的作用**：

前端可以通过poll `/session-stats` 获取：
```javascript
// 前端伪代码
async function monitorSession() {
  while (true) {
    const stats = await fetch('/session-stats').then(r => r.json());
    const session = stats.sessions[0];
    
    if (session.state === 'running') {
      // 正常播放
      element.style.display = 'block';
      status.textContent = '正在直播';
    } else if (session.state === 'reconnecting') {
      // 重连中
      element.style.display = 'none';
      status.textContent = '重连中...';
    } else if (session.state === 'error') {
      // 错误
      status.textContent = '连接失败';
    }
    
    // 检查最后活跃时间
    const lastTime = new Date(session.last_frame_time);
    const now = new Date();
    const lag = (now - lastTime) / 1000; // 秒
    
    if (lag > 10) {
      status.textContent = `已卡顿 ${Math.round(lag)} 秒`;
    }
    
    await sleep(500);
  }
}
```

---

### 6. SourceKey归一化

#### 问题背景

不同的URL表示可能导致创建多个session：

```
❌ 不同形式的同一URL：
   https://example.com/stream.flv?token=xxx&id=1
   https://example.com/stream.flv?id=1&token=xxx  ← 查询参数顺序不同
   https://example.com/stream.flv?id=1&token=xxx&v=2  ← 附加参数
   http://example.com/stream.flv  ← 协议不同

结果：创建4个session，占用4倍资源！
```

#### 归一化流程

```
原始URL
  ↓
1. 解码（urldecode）
   example.com/stream.flv?id=1&token=abc%20def
   → example.com/stream.flv?id=1&token=abc def
  ↓
2. 规范化协议
   http/https → https
   rtmp/rtmps → rtmps
  ↓
3. 排序查询参数
   ?id=1&token=xxx&v=2
   → ?id=1&token=xxx&v=2  (已排序)
  ↓
4. 移除无关参数
   ✅ 保留：token, id, expire, sign（认证相关）
   ❌ 删除：cache_bust, _ts, timestamp（反缓存参数）
  ↓
5. 生成SourceKey
   SourceKey(
     kind='flv',
     value='https://example.com/stream.flv?id=1&token=xxx',
     camera_id='camera3'
   )
```

#### 实际例子

```python
# 前端可能发送（多种形式）：
[
  'https://example.com/stream.flv?id=1&token=abc&_ts=123456',
  'https://example.com/stream.flv?token=abc&id=1&cache=1',
  'https://example.com/stream.flv?id=1&token=abc'
]

# 归一化后（全部相同）：
[
  'https://example.com/stream.flv?id=1&token=abc',
  'https://example.com/stream.flv?id=1&token=abc',
  'https://example.com/stream.flv?id=1&token=abc'
]

# 结果：
✅ 1个session，3个WebSocket订阅者
❌ 3个session，浪费资源
```

#### 归一化规则（实现于 `SourceKey.__init__`）

```
kind 标准化：
  'flv' / 'FLV' → 'flv'
  'mpv' / 'mpvpipe' → 'flv'（都是通过mpv拉FLV）
  'rtsp' / 'RTSP' → 'rtsp'

value 归一化：
  1. urldecode  （前端已做，再做一遍保险）
  2. parse URL
  3. 规范化协议（http→https）
  4. 删除反缓存参数（_ts, cache_bust等）
  5. 排序查询参数
  6. 重建URL

camera_id 标准化：
  保持原值（但检查大小写一致性）
```

---

### 7. 日志示例完整流程

#### 初始化阶段

```
[SESSION] Created source_key=flv:https://...@camera3 session_id=140001 stream_id=220001
[PIPELINE-START] source_key=... start_count=1 reader_thread=Thread-1 infer_thread=Thread-2
[Infer] ... started
[Reader] ... started
```

#### 正常运行阶段

```
[INFER] source_key=... infer_count=10 frame_no=50 subscriber_count=1
[INFER] source_key=... infer_count=20 frame_no=100 subscriber_count=1
[BROADCAST] source_key=... frame_id=10 subscriber_count=1
[SEND] source_key=... ws_id=140002 frame_id=10
```

#### WebSocket用户接入

```
[WS] New connection: kind=flv, value=https://...@camera3
[WS] DECODED value = https://...@camera3
[WS] Source key: SourceKey(flv:https://...@camera3)
[SESSION-REUSE] source_key=... session_id=140001 ref_count=1
[INFER] source_key=... infer_count=30 subscriber_count=2  ← 订阅者增加
[BROADCAST] source_key=... subscriber_count=2
[SEND] source_key=... ws_id=140002 frame_id=20
[SEND] source_key=... ws_id=140003 frame_id=20  ← 同一帧发给两个ws
```

#### 丢帧重连

```
[Detection] Lost frames from camera 7, attempting reconnection
[Reconnect] Stage 1 - Attempt 1/4 for camera 7
[Reconnect] Stage 1 - Successfully connected camera 7
[PIPELINE-START] source_key=... start_count=2  ← 重新启动
[INFER] source_key=... infer_count=50 subscriber_count=2
```

#### 断开清理

```
[WS] Client disconnected
[WS] Unregistered from session: ...
[INFER] source_key=... infer_count=100 subscriber_count=1  ← 订阅者减少
[Detection] Stopping detection for camera 7
[SourceSessionManager] Cleaned up idle session: ...  ← TTL后自动清理
```

---

## 🚀 部署指南

### Windows 开发环境

```bash
# 1. 安装依赖
pip install fastapi uvicorn opencv-python ultralytics numpy

# 2. 下载 mpv
# 访问 https://mpv.io/installation/ 下载 Windows 版本
# 解压到 D:\mpv\

# 3. 修改配置
# config.py:
PT_MODEL_PATH = r"E:\path\to\your\model.pt"
MPV_EXE = r"D:\mpv\mpv-x86_64-xxx\mpv.exe"

# 4. 启动服务
python run.py
# 访问 http://127.0.0.1:8080
```

### RK3588 部署

```bash
# 1. 安装 RKNN Lite2
pip install rknn-toolkit-lite2

# 2. 转换模型
# 在 PC 上使用 rknn-toolkit2 转换 .pt → .rknn
# 参考：https://github.com/airockchip/rknn-toolkit2

# 3. 修改配置
# config.py:
USE_RKNN = True
YOLO_MODEL_PATH = "/path/to/model.rknn"
RKNN_CORE_MASK = RKNNLite.NPU_CORE_0_1_2  # 使用 3 核 NPU

# 4. 启动
python run.py --host 0.0.0.0 --port 8080
```

---

## 📡 WebSocket API

### 连接端点

```
ws://localhost:8080/ws?kind={source_type}&value={source_path}
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `kind` | string | 是 | 视频源类型 |
| `value` | string | 否 | 源路径/URL（URL 需 urlencode） |

### 示例

```javascript
// HLS 直播流
const ws = new WebSocket(
  'ws://localhost:8080/ws?kind=mpv&value=' + 
  encodeURIComponent('https://example.com/live.m3u8')
);

// RTSP 摄像头
const ws = new WebSocket(
  'ws://localhost:8080/ws?kind=rtsp&value=' + 
  encodeURIComponent('rtsp://admin:pass@192.168.1.100:554/stream')
);

// 本地文件
const ws = new WebSocket(
  'ws://localhost:8080/ws?kind=file&value=' + 
  encodeURIComponent('C:/videos/test.mp4')
);
```

### 数据格式

**服务端 → 客户端**：
- Base64 编码的 JPEG 图片
- 每帧包含检测框和 FPS 信息

```javascript
ws.onmessage = (event) => {
  const img = new Image();
  img.src = 'data:image/jpeg;base64,' + event.data;
  document.getElementById('video').src = img.src;
};
```

---

## ⚙️ 性能调优

### 1. 延迟优化

```python
# config.py
QUEUE_MAX = 2           # 队列越小延迟越低（但更易丢帧）
FRAME_INTERVAL = 1      # 每帧都推理（延迟最低）
MAX_FPS = 30            # 提高推送帧率
```

### 2. 吞吐量优化

```python
# config.py
QUEUE_MAX = 10          # 队列变大，减少丢帧
FRAME_INTERVAL = 3      # 每 3 帧推理一次（提升吞吐）
MAX_FPS = 15            # 降低推送帧率节省带宽
```

### 3. 带宽优化

```python
# config.py
JPEG_QUALITY = 60       # 降低画质（从 80 → 60）
IMG_SIZE = (320, 320)   # 降低推理分辨率
MPV_PIPE_W = 640        # 降低 MPV 输出分辨率
```

### 4. RK3588 NPU 优化

```python
# config.py
RKNN_CORE_MASK = RKNNLite.NPU_CORE_0_1_2  # 使用全部 3 核
IMG_SIZE = (640, 640)   # RK3588 对 640x640 优化最好
```

---

## 🐛 常见问题

### 1. MPV 启动失败

**症状**：`[MPVPIPE] mpv exited rc=1`

**解决方案**：
```bash
# 检查 mpv 是否安装
D:\mpv\mpv.exe --version

# 检查路径配置
# config.py:
MPV_EXE = r"D:\mpv\mpv-x86_64-20260104-git-a3350e2\mpv.exe"  # 改成实际路径
```

### 2. HEVC 解析错误

**症状**：`[ffmpeg] hevc: Failed to parse header of NALU`

**原因**：视频流编码有问题或不完整

**解决方案**：
```python
# config.py - 添加更宽松的解析参数
MPV_EXTRA_OPTS = [
    "--demuxer-lavf-o=analyzeduration=10000000",
    "--demuxer-lavf-o=probesize=50000000",
]
```

### 3. 帧率不稳定

**症状**：FPS 忽高忽低

**排查步骤**：
1. 检查 Reader 线程是否稳定
2. 检查推理时间是否超过帧间隔
3. 检查网络带宽是否足够

```python
# 调试日志
# main.py - reader() 函数中已有：
if time.time() - last > 1:
    print(f"READER fps≈{cnt}")  # 查看读取帧率
```

### 4. WebSocket 断连

**症状**：连接频繁断开

**解决方案**：
```python
# 添加心跳保活
async def keep_alive(ws):
    while True:
        await asyncio.sleep(30)
        await ws.send_text("ping")
```

### 5. 内存泄漏

**症状**：运行一段时间后内存持续增长

**排查**：
```python
# 检查队列是否清理
# main.py - 确保每次循环都清空旧帧：
while not frame_queue.empty():
    frame_queue.get_nowait()  # ✅ 正确
```

---

## 📝 开发建议

### 代码规范

1. **异常处理**：所有 I/O 操作必须 try-catch
2. **资源释放**：使用 `try-finally` 或上下文管理器
3. **日志记录**：关键路径添加 DEBUG 日志

### 扩展开发

#### 添加新的视频源

```python
# streams.py
class MyCustomStream:
    def __init__(self, url):
        # 初始化连接
        pass
    
    def read(self):
        # 返回 (ok: bool, frame: np.ndarray)
        return True, frame
    
    def release(self):
        # 清理资源
        pass

# 注册到 open_source
def open_source(kind, value):
    if kind == "mycustom":
        return MyCustomStream(value)
```

#### 添加新的检测类别

```python
# config.py
CLASSES = ("standing", "mating", "lying", "new_class")  # 添加新类别
NUM_CLASSES = 4

# overlays.py
_COLOR_MAP = {
    0: (0, 255, 0),
    1: (0, 0, 255),
    2: (255, 0, 0),
    3: (255, 255, 0),  # 新类别颜色
}
```

---

