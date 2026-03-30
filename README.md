# donkey-behavior-platform
mpv --msg-level=all=info "https://rtmp16open.ys7.com:9188/v3/openlive/FR3098735_1_2.flv?expire=1800587241&id=936215804142804992&t=0eb0338f4838334a4678607eea51a22945260c886fb51c471c5fd5e0fc75de74&ev=101&supportH265=1"
探测萤石云摄像头FLV数据量的 分辨率、帧率：
● Video  --vid=1  (hevc 704x576 25 fps)
● Audio  --aid=1  (pcm_alaw 1ch 8000 Hz 64 kbps)
AO: [wasapi] 48000Hz stereo 2ch float
VO: [gpu-next] 704x576 yuv420p

# 前后端服务部署指南
根据我对项目结构的分析，这是一个基于 Python FastAPI 后端和 Vue 3 前端的实时检测系统。下面是完整的部署方案，让您的服务可以通过网址被所有人访问。

## 一、部署架构选择
### 1. 云服务器选择
推荐使用以下云服务提供商：

- 阿里云 ：ECS 实例
- 腾讯云 ：CVM 实例
- 华为云 ：ECS 实例
- AWS ：EC2 实例
配置建议：

- 最低配置 ：2核4G内存，50G存储
- 推荐配置 ：4核8G内存，100G存储（如果检测任务较重）
### 2. 操作系统选择
- 推荐 ：Ubuntu 22.04 LTS（稳定且易于配置）
- 备选 ：CentOS 7/8
## 二、后端部署步骤
### 1. 服务器初始化
```
# 更新系统
sudo apt update && sudo apt upgrade 
-y

# 安装必要工具
sudo apt install -y git python3 
python3-pip python3-venv nginx 
certbot
```
### 2. 项目部署
```
# 克隆项目
git clone <你的项目仓库地址> /var/www/
realtime-detector
cd /var/www/realtime-detector

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```
### 3. 配置 uvicorn 服务
创建 systemd 服务文件：

```
sudo nano /etc/systemd/system/
realtime-detector.service
```
内容如下：

```
[Unit]
Description=Realtime Detector API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/
realtime-detector
Environment="PATH=/var/www/
realtime-detector/venv/bin"
ExecStart=/var/www/realtime-detector/
venv/bin/uvicorn modules.main:app 
--host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
启动服务：

```
sudo systemctl daemon-reload
sudo systemctl start 
realtime-detector
sudo systemctl enable 
realtime-detector
```
## 三、前端部署步骤
### 1. 构建前端项目
```
cd /var/www/realtime-detector/
vue-frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```
构建完成后，前端文件会生成在 dist 目录中。

### 2. 配置 Nginx 代理
创建 Nginx 配置文件：

```
sudo nano /etc/nginx/sites-available/
realtime-detector
```
内容如下：

```
server {
    listen 80;
    server_name your-domain.com;  # 
    替换为你的域名

    # 前端静态文件
    location / {
        root /var/www/
        realtime-detector/
        vue-frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.
        html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://
        localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade 
        $http_upgrade;
        proxy_set_header Connection 
        'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass 
        $http_upgrade;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://
        localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade 
        $http_upgrade;
        proxy_set_header Connection 
        "upgrade";
    }
}
```
启用配置：

```
sudo ln -s /etc/nginx/
sites-available/realtime-detector /
etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```
## 四、域名和 SSL 配置
### 1. 域名解析
- 在你的域名提供商处，将域名 A 记录指向服务器的公网 IP 地址
### 2. 配置 SSL 证书
使用 Let's Encrypt 免费证书：

```
sudo certbot --nginx -d your-domain.
com
```
按照提示完成配置，certbot 会自动更新 Nginx 配置以启用 HTTPS。

## 五、环境变量配置
根据项目需求，可能需要配置一些环境变量。创建 .env 文件：

```
nano /var/www/realtime-detector/.env
```
内容示例：

```
# 数据库配置
DATABASE_URL="sqlite:///./detector.
db"

# 其他配置
SECRET_KEY="your-secret-key"
```
## 六、启动和测试
### 1. 检查服务状态
```
sudo systemctl status 
realtime-detector
sudo systemctl status nginx
```
### 2. 测试访问
- 前端： https://your-domain.com
- 后端 API： https://your-domain.com/api
## 七、监控和维护
### 1. 日志查看
```
# 后端日志
sudo journalctl -u realtime-detector

# Nginx 日志
sudo tail -f /var/log/nginx/access.
log
sudo tail -f /var/log/nginx/error.log
```
### 2. 自动更新证书
Let's Encrypt 证书有效期为 90 天，设置自动更新：

```
sudo systemctl enable certbot.timer
```
### 3. 定期备份
设置定期备份脚本，备份数据库和重要配置文件。

## 八、扩展和优化
### 1. 性能优化
- 使用 Gunicorn + uvicorn 提高并发性能
- 配置 Nginx 缓存
- 启用 HTTP/2
### 2. 安全加固
- 配置防火墙
- 禁用不必要的服务
- 定期更新系统和依赖
## 总结
通过以上步骤，您的实时检测系统将成功部署到云服务器上，并可以通过域名被所有人访问。部署完成后，您可以根据实际运行情况进行进一步的优化和调整。

如果在部署过程中遇到任何问题，请随时咨询。

1. 你怎么通过 WebSocket 接收处理后的实时画面的？

我这套实时检测链路是“后端处理帧，前端只接结果”的思路。
前端进入实时检测页后，会调用我封装的 useWebSocket，根据当前选择的摄像头或视频源类型，拼出 /ws?kind=...&value=... 这样的 WebSocket 地址，然后建立连接。连接成功后，前端主要监听 onmessage，后端每推来一帧数据，我就把这一帧直接更新到 frame 这个响应式变量里。前端如果收到的是 ERROR:: 开头的文本，就当成错误信息展示，而不是当成图像帧。组件卸载时我会主动断开连接，避免重复连接和资源泄漏。

后端这边，/ws 这个接口在接到连接后，会先根据 kind 和 value 打开对应视频源，然后启动一个双线程流水线：一个 Reader 线程持续读最新帧，一个 Infer 线程按设定间隔做推理、画框、叠加 FPS，并把处理后的最新帧放进结果队列。主协程则不断从结果队列里取最新帧，通过 ws_manager.send_frame() 发给前端。

真正发送时，后端会先把 OpenCV 的帧编码成 JPEG，再做 Base64，最后通过 ws.send_text() 发给前端。所以前端拿到的其实不是原始视频流协议，而是一帧一帧已经处理好的 JPEG 图像数据。

2. 前端怎么配合实时检测展示的？

前端配合实时检测，核心做了三件事。
第一，管理连接生命周期。页面进入时建立 WebSocket，页面离开时关闭 WebSocket，防止多次进入页面后出现重复推流、重复渲染的问题。这个清理逻辑我是放在 onUnmounted 里的。

第二，只消费最新结果。因为这是实时监控场景，我更关心“当前最新状态”，而不是把所有帧都缓存下来。后端结果队列只保留最新帧，前端也是收到一帧就覆盖当前显示内容，不做历史帧堆积，这样延迟更低，也不容易把页面越跑越卡。后端 Reader 线程会清空旧帧队列，只保留最新输入帧；Infer 线程也会清空旧结果，只保留最新输出帧。

第三，把后端检测结果稳定可视化。后端推过来的帧已经画好了检测框和 FPS，所以前端不用再自己算框位置或做额外绘制，只需要把 Base64 图像渲染出来就行。这样前后端职责分得比较清楚：后端负责推理、画框和帧率控制，前端负责连接管理、状态展示和交互体验。后端还在 WSManager 里做了最大 FPS 控制，避免推送过快占满带宽或让前端频繁重渲染。

3. 这一套方案的设计思路是什么？

我的设计思路是把“实时检测”拆成两条链路：
一条是检测处理链路，放在后端完成，包括读帧、推理、画框、JPEG 编码；
另一条是结果展示链路，放在前端完成，包括建连、收帧、错误提示、页面渲染。

这样做的好处是前端足够轻，不需要处理复杂视频解码和框绘制；后端可以统一控制推理频率、JPEG 质量和推送帧率。比如后端在推送前会按 max_fps 控制发送间隔，并把帧压成 JPEG 后再 Base64 发送。

从全栈角度看，这其实是“HTTP 做管理类接口，WebSocket 做实时展示”的分工：管理页面还是走普通 REST API，而实时检测这种高频更新场景，用 WebSocket 更合适。

## FLV流分析

### 分辨率
- 视频流分辨率：1280x720（720p）
- 模型输入分辨率：640x640

### 抽帧间隔
- 流处理帧率：15 FPS
- 抽帧间隔：约66.7毫秒（1/15秒）
- 最大帧率限制：20 FPS

### 每秒运算量
- 每秒处理15帧图像
- 每帧图像需要经过以下处理：
  1. 视频解码（通过mpv）
  2. 图像缩放（1280x720 → 640x640）
  3. YOLO模型推理（检测standing、mating、lying三类）
  4. 结果后处理和事件检测

### 性能评估
- 模型推理：每帧需要处理640x640的图像，包含3个类别的检测
- 事件检测：需要持续分析检测结果，判断mating事件（最少持续6秒）
- 网络传输：需要实时传输处理后的视频流到前端

### 优化建议
- 可根据硬件性能调整MPV_PIPE_FPS参数
- 对于低配置设备，可降低分辨率或帧率以提高性能
- 考虑使用硬件加速解码以减少CPU占用

## 项目框架结构

### 整体架构
```
realtime-detector/
├── backend/           # 后端代码
├── data/              # 数据存储
├── modules/           # 核心模块
├── static/            # 静态文件
├── uploads/           # 上传文件
├── vue-frontend/      # 前端代码
├── .env               # 环境变量
├── requirements.txt   # 后端依赖
└── README.md          # 项目文档
```

### 详细文件结构与作用

#### 1. backend/ - 后端代码
```
backend/
├── apis/             # API接口
│   ├── barn.py       # 养殖舍相关API
│   ├── camera.py     # 摄像头相关API
│   ├── event.py      # 事件相关API
│   ├── pen.py        # 栏相关API
│   └── upload.py     # 文件上传API
├── models/           # 数据模型
│   ├── barn.py       # 养殖舍模型
│   ├── camera.py     # 摄像头模型
│   ├── event.py      # 事件模型
│   └── pen.py        # 栏模型
├── schemas/          # 数据验证
│   ├── barn.py       # 养殖舍数据结构
│   ├── camera.py     # 摄像头数据结构
│   ├── event.py      # 事件数据结构
│   └── pen.py        # 栏数据结构
└── utils/            # 工具函数
```

**作用**：
- `apis/`：提供RESTful API接口，处理前端请求
- `models/`：定义数据库模型，处理数据存储和查询
- `schemas/`：定义数据传输对象，验证请求和响应数据
- `utils/`：提供通用工具函数，如数据库连接、文件处理等

#### 2. data/ - 数据存储
```
data/
└── farm.db           # SQLite数据库文件
```

**作用**：
- 存储系统数据，包括养殖舍、栏、摄像头、事件等信息

#### 3. modules/ - 核心模块
```
modules/
├── config.py         # 配置文件
├── detector.py       # 目标检测模块
├── main.py           # 主应用入口
└── utils.py          # 模块工具函数
```

**作用**：
- `config.py`：定义系统配置参数，如队列大小、帧间隔等
- `detector.py`：实现目标检测逻辑，包括模型加载、推理等
- `main.py`：主应用入口，包含WebSocket处理、检测线程管理等
- `utils.py`：提供模块级工具函数，如视频流处理、帧转换等

#### 4. static/ - 静态文件
```
static/
└── mating_screenshots/  # 交配事件截图
```

**作用**：
- 存储事件截图，供前端展示

#### 5. uploads/ - 上传文件
```
uploads/
```

**作用**：
- 存储用户上传的视频和图片文件

#### 6. vue-frontend/ - 前端代码
```
vue-frontend/
├── public/           # 公共资源
├── src/              # 源代码
│   ├── assets/       # 静态资源
│   ├── components/   # 组件
│   │   ├── BarnSelect.vue       # 养殖舍选择组件
│   │   ├── EventRecord.vue      # 事件记录组件
│   │   └── PenSelect.vue        # 栏选择组件
│   ├── composables/  # 组合式函数
│   │   ├── useApi.ts           # API调用封装
│   │   ├── useWebSocket.ts     # WebSocket封装
│   │   └── useEventStore.ts    # 事件状态管理
│   ├── pages/        # 页面
│   │   ├── Detection.vue       # 检测页面
│   │   ├── Events.vue          # 事件页面
│   │   └── Settings.vue        # 设置页面
│   ├── router/       # 路由
│   ├── stores/       # 状态管理
│   ├── types/        # TypeScript类型定义
│   ├── App.vue       # 根组件
│   └── main.ts       # 前端入口
├── index.html        # HTML模板
├── package.json      # 前端依赖
└── vite.config.ts    # Vite配置
```

**作用**：
- `components/`：前端组件，如养殖舍选择、事件记录等
- `composables/`：组合式函数，封装API调用、WebSocket连接等
- `pages/`：前端页面，如检测页面、事件页面等
- `router/`：前端路由配置
- `stores/`：前端状态管理

### 核心功能模块

#### 1. 实时检测模块
- **位置**：`modules/main.py`
- **功能**：处理视频流、目标检测、WebSocket通信
- **关键函数**：
  - `start_detection()`：启动检测线程
  - `infer()`：执行目标检测推理
  - `check_and_process_mating()`：检测和处理交配事件

#### 2. 目标检测模块
- **位置**：`modules/detector.py`
- **功能**：加载模型、执行推理、绘制检测框
- **关键函数**：
  - `infer_once()`：执行单次推理
  - `annotate()`：在帧上绘制检测结果

#### 3. 事件管理模块
- **位置**：`backend/models/event.py`
- **功能**：管理交配事件的存储和查询
- **关键函数**：
  - `create()`：创建新事件
  - `get_all()`：获取所有事件
  - `get_by_camera()`：按摄像头获取事件

#### 4. 前端API调用模块
- **位置**：`vue-frontend/src/composables/useApi.ts`
- **功能**：封装API调用，处理文件上传等
- **关键函数**：
  - `uploadFile()`：上传文件
  - `getEvents()`：获取事件列表
  - `deleteFile()`：删除文件

#### 5. WebSocket通信模块
- **位置**：`vue-frontend/src/composables/useWebSocket.ts`
- **功能**：管理WebSocket连接，接收实时视频流
- **关键函数**：
  - `connect()`：建立WebSocket连接
  - `disconnect()`：断开WebSocket连接
  - `sendMessage()`：发送消息

### 数据流

1. **实时检测流程**：
   - 前端选择摄像头 → 建立WebSocket连接 → 后端启动检测线程 → 处理视频流 → 执行目标检测 → 绘制检测结果 → 通过WebSocket推送帧数据 → 前端展示

2. **文件上传流程**：
   - 前端选择文件 → 调用uploadFile() → 后端接收文件 → 保存文件 → 执行检测 → 返回检测结果 → 前端展示

3. **事件管理流程**：
   - 后端检测到交配事件 → 保存事件到数据库 → 前端调用getEvents() → 后端返回事件列表 → 前端展示事件记录

### 关键配置参数

| 配置项 | 位置 | 作用 |
|-------|------|------|
| QUEUE_MAX | modules/config.py | 帧队列最大长度 |
| FRAME_INTERVAL | modules/config.py | 推理帧间隔 |
| MPV_PIPE_FPS | modules/config.py | 视频流处理帧率 |
| MAX_FPS | modules/main.py | 最大推送帧率 |
| CONF_THRESHOLD | modules/detector.py | 置信度阈值 |
| MIN_EVENT_DURATION | modules/main.py | 最小事件持续时间 |

### 技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 后端 | Python | 3.8+ | 核心逻辑实现 |
| 后端框架 | FastAPI | 0.104+ | API接口和WebSocket |
| 前端 | Vue | 3.3+ | 前端界面 |
| 前端状态管理 | Pinia | 2.1+ | 状态管理 |
| 数据库 | SQLite | 3.35+ | 数据存储 |
| 视频处理 | mpv | 0.35+ | 视频流获取和处理 |
| 目标检测 | YOLO | v8 | 目标检测模型 |
| 部署 | Nginx | 1.18+ | 反向代理 |

### 排查指南

1. **实时检测问题**：
   - 检查WebSocket连接是否正常
   - 查看后端日志中的检测结果
   - 验证视频流地址是否正确

2. **文件上传问题**：
   - 检查Nginx配置中的文件大小限制
   - 查看后端日志中的上传错误
   - 验证文件路径权限

3. **事件记录问题**：
   - 检查数据库连接是否正常
   - 查看事件保存逻辑
   - 验证事件查询API是否正确

4. **性能问题**：
   - 调整帧间隔和推理频率
   - 检查CPU和内存使用情况
   - 优化视频流处理参数

通过以上项目框架的整理，您可以更清晰地了解系统的结构和功能，便于排查和理解各个模块的作用。