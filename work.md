# 实时检测系统工作流程

## 项目概述

本项目是一个基于Vue 3 + TypeScript的前端和FastAPI后端的实时检测系统，主要功能包括：
- 本地视频/图片文件上传与检测
- 摄像头视频流实时检测
- 养殖舍、栏、摄像头管理
- 交配行为识别与事件记录
- WebSocket实时通信

## 技术栈

### 前端
- Vue 3 + Composition API
- TypeScript
- Pinia状态管理
- Vue Router路由管理
- Axios HTTP客户端
- WebSocket实时通信

### 后端
- FastAPI
- SQLite数据库
- OpenCV图像处理
- YOLOv8目标检测
- WebSocket服务

## 工作流程

### 1. 开发环境搭建

#### 前端环境
1. 安装Node.js和npm
2. 进入`vue-frontend`目录
3. 安装依赖：`npm install`
4. 启动开发服务器：`npm run dev`

#### 后端环境
1. 安装Python 3.8+
2. 安装依赖：`pip install -r requirements.txt`
3. 启动后端服务器：`python run.py` 或 `uvicorn modules.main:app --host 0.0.0.0 --port 8000`

### 2. 前后端联调流程

#### 2.1 API连接测试
1. 前端通过Axios发送请求到后端API
2. 测试健康检查接口：`GET /health`
3. 测试养殖舍列表接口：`GET /api/barns`

#### 2.2 文件上传与检测
1. 前端选择本地文件（视频/图片）
2. 通过`POST /upload`接口上传文件
3. 后端保存文件并返回文件路径
4. 前端使用WebSocket连接到`/ws`端点，传递文件路径
5. 后端启动检测流程，通过WebSocket返回实时帧
6. 前端接收并显示检测结果
7. 点击停止按钮，前端通过`DELETE /upload/{filename}`删除上传的文件

#### 2.3 数据管理功能
1. 养殖舍管理：增删改查操作
2. 栏管理：增删改查操作
3. 摄像头管理：增删改查操作
4. 事件记录：查询交配事件

### 3. 前后端联调重点

#### 3.1 跨域问题
- 后端使用FastAPI的CORS中间件，允许所有来源的跨域请求
- 前端Axios配置基础URL为后端地址

#### 3.2 WebSocket通信
- 前端使用WebSocket连接与后端实时通信
- 后端通过WebSocket发送检测结果帧
- 处理WebSocket连接断开和重连

#### 3.3 文件上传与删除
- 前端使用FormData上传文件
- 后端保存文件到`uploads`目录
- 停止检测时删除已上传的文件

#### 3.4 响应式设计
- 前端使用媒体查询适配不同屏幕尺寸
- 确保在移动设备上的良好显示效果

## 注意事项

### 1. 性能优化
- 后端使用线程池处理视频流和检测
- 前端使用虚拟滚动处理大量数据
- 合理使用缓存减少API请求

### 2. 错误处理
- 前端添加请求错误处理和用户提示
- 后端添加异常捕获和错误响应
- 网络错误和服务器错误的优雅处理

### 3. 安全性
- 后端验证文件上传类型和大小
- 防止路径遍历攻击
- 敏感信息保护

### 4. 部署考虑
- 前端构建：`npm run build`
- 后端依赖管理
- 服务器配置和端口设置

## 全栈面试准备

### 1. 项目架构理解
- 前后端分离架构
- 数据流设计
- 组件化开发

### 2. 技术选型理由
- 为什么选择Vue 3 + TypeScript
- 为什么选择FastAPI
- 为什么使用WebSocket

### 3. 核心功能实现
- 文件上传与处理流程
- WebSocket实时通信实现
- 视频流处理和检测算法集成


#### 前端相关
1. **Vue 3 Composition API的优势？**
   - 更好的代码组织和复用
   - 类型推断支持
   - 更灵活的逻辑组合

2. **如何处理WebSocket连接？**
   - 使用`useWebSocket` composable封装WebSocket逻辑
   - 处理连接、断开、重连
   - 实时数据更新和错误处理

3. **响应式设计实现？**
   - 使用媒体查询适配不同屏幕尺寸
   - 灵活的布局系统
   - 组件的自适应调整

#### 后端相关
1. **FastAPI的优势？**
   - 自动生成API文档
   - 类型提示和验证
   - 高性能（基于Starlette）

2. **如何处理文件上传？**
   - 使用FastAPI的`UploadFile`类型
   - 保存文件到指定目录
   - 安全检查和错误处理

3. **WebSocket服务实现？**
   - 使用FastAPI的WebSocket支持
   - 管理多个连接
   - 实时数据传输

#### 全栈相关
1. **前后端联调的挑战？**
   - 跨域问题
   - 数据格式一致性
   - 实时通信可靠性

2. **如何优化系统性能？**
   - 前端：组件懒加载、虚拟滚动
   - 后端：线程池、缓存策略
   - 网络：WebSocket优化、数据压缩

3. **系统架构设计考虑？**
   - 模块化设计
   - 可扩展性
   - 容错机制


## 完整业务流程：从选择摄像头到检测结果显示

### 1. 用户选择流程

1. **前端加载养殖舍列表**
   - 组件挂载时调用 `loadBarns()` 方法
   - 通过 Pinia store 的 `fetchBarns()` 从后端获取养殖舍数据
   - 后端 API：`GET /api/barns`

2. **用户选择1舍**
   - 前端 `selectedBarn` 值更新为1
   - 触发 `loadPens()` 方法获取该养殖舍下的栏列表
   - 后端 API：`GET /api/barns/1/pens`

3. **用户选择1栏**
   - 前端 `selectedPen` 值更新为1
   - 触发 `loadCameras()` 方法获取该栏下的摄像头列表
   - 后端 API：`GET /api/pens/1/cameras`

4. **用户选择1号摄像头**
   - 前端 `selectedCamera` 值更新为1号摄像头的 FLV 地址

### 2. 启动检测流程

1. **前端点击"开始"按钮**
   - 调用 `start()` 方法
   - 检查是否选择了摄像头
   - 设置 `kind` 为 "mpv"（用于处理 FLV 流）
   - 调用 `connect(kind, value)` 建立 WebSocket 连接

2. **WebSocket 连接建立**
   - 前端连接到后端 WebSocket 端点：`ws://localhost:8000/ws`
   - 传递参数：`kind=mpv` 和 `value=<摄像头FLV地址>`

3. **后端处理**
   - 接收 WebSocket 连接
   - 调用 `open_source(kind, value)` 打开视频流
   - 启动 `start_pipeline()` 函数处理视频流
   - 创建两个线程：
     - `reader()`：读取视频帧
     - `infer()`：进行目标检测和行为识别

### 3. 实时检测与显示

1. **后端检测流程**
   - `reader()` 线程不断读取视频帧并放入队列
   - `infer()` 线程从队列取出帧进行检测
   - 使用 YOLOv8 模型进行目标检测
   - 使用对比学习模型识别交配行为
   - 对检测结果进行标注
   - 将标注后的帧放入结果队列

2. **WebSocket 数据传输**
   - 后端从结果队列取出最新帧
   - 将帧编码为 base64 格式
   - 通过 WebSocket 发送给前端

3. **前端显示**
   - 接收 WebSocket 消息
   - 解析 base64 数据
   - 更新 `frame` 状态
   - 通过 `<img>` 标签显示实时画面

### 4. 交配行为检测与记录

1. **后端检测到交配行为**
   - 当检测到交配行为时，记录相关信息：
     - 摄像头ID
     - 栏ID
     - 养殖舍ID
     - 开始时间
     - 结束时间
     - 持续时间
     - 置信度
     - 截图

2. **后端记录事件**
   - 调用 `MatingEvent.create()` 方法
   - 将事件数据插入 SQLite 数据库
   - 后端 API：`POST /api/mating-events`

### 5. 停止检测流程

1. **前端点击"停止"按钮**
   - 调用 `stop()` 方法
   - 调用 `disconnect()` 关闭 WebSocket 连接

2. **后端清理**
   - 接收到 WebSocket 断开事件
   - 停止后台线程
   - 释放视频流资源
   - 清理 WebSocket 连接

## 项目启动步骤

1. **启动后端服务器**
   ```bash
   cd e:\donkey\萤石云\realtime-detector
   python run.py
   ```

2. **启动前端开发服务器**
   ```bash
   cd e:\donkey\萤石云\realtime-detector\vue-frontend
   npm run dev
   ```

3. **访问前端页面**
   - 打开浏览器，访问 `http://localhost:5173`

4. **测试功能**
   - 选择本地文件（视频/图片）进行检测
   - 测试摄像头流检测
   - 测试数据管理功能
