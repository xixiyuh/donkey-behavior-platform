# Vue 3 + Vite

## 项目概述

本项目是一个基于Vue 3 + TypeScript + Pinia + Vue Router的前端项目，用于实时视频检测和分析。

## 技术栈

- Vue 3 (Composition API)
- TypeScript
- Pinia (状态管理)
- Vue Router (路由管理)
- Axios (HTTP客户端)
- WebSocket (实时通信)

## 今天修改的技术细节

### 1. 加载状态管理优化
- **修改文件**: `src/components/Detection.vue`
- **修改内容**: 优化了WebSocket连接状态的监听逻辑，当连接状态改变时（无论是连接成功还是关闭），都会重置加载状态，确保检测画面能够正确显示。
- **业务逻辑**: 当用户点击开始检测时，系统显示加载动画；WebSocket连接成功后，加载动画关闭并显示检测画面；当连接关闭时，加载状态也会被重置，避免加载动画一直显示。
- **伪代码**:
  ```javascript
  // 监听连接状态变化
  watch(isConnected, (newValue) => {
    // 无论是连接成功还是关闭，都关闭加载状态
    isLoading.value = false;
  });
  ```

### 2. 文件删除机制改进
- **修改文件**: `src/components/Detection.vue`
- **修改内容**: 增加了删除文件前的延迟时间，从3秒增加到5秒，确保后端有足够的时间释放文件资源。
- **业务逻辑**: 当用户点击停止检测时，系统先断开WebSocket连接，然后等待5秒让后端释放文件资源，最后尝试删除上传的文件，避免文件被占用的错误。
- **伪代码**:
  ```javascript
  const stop = async () => {
    disconnect();
    isLoading.value = false;
    
    // 等待后端释放文件资源
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // 删除上传的文件
    if (currentFileName.value) {
      await deleteFile(currentFileName.value);
    }
  };
  ```

### 3. 流资源释放优化
- **修改文件**: `modules/main.py` (后端)
- **修改内容**: 在reader线程的finally块中添加了流资源释放的代码，确保即使在异常情况下，流资源也能被正确释放。
- **业务逻辑**: 当视频流结束或发生异常时，系统会自动释放流资源，避免文件被占用，确保前端能够成功删除文件。
- **伪代码**:
  ```python
  def reader():
      try:
          while not stop_event.is_set():
              ok, frame = stream.read()
              # 处理帧数据
      except Exception as e:
          print(f"READER thread error: {e}")
      finally:
          print("READER thread stopped")
          # 确保流资源被释放
          try:
              if hasattr(stream, 'release'):
                  stream.release()
                  print("[READER] Stream released in finally block")
          except Exception as e:
              print(f"[READER] Error releasing stream in finally: {e}")
  ```

### 4. 文件选择处理改进
- **修改文件**: `src/components/Detection.vue`
- **修改内容**: 在处理新文件之前先断开现有连接，避免并发操作导致的冲突。
- **业务逻辑**: 当用户选择新文件时，系统会先断开现有连接，然后上传新文件并启动检测，确保每次文件选择都能正确处理，避免并发操作导致的冲突。
- **伪代码**:
  ```javascript
  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    
    // 先断开现有连接，避免冲突
    if (isConnected.value) {
      disconnect();
      isLoading.value = false;
    }
    
    // 上传文件并启动检测
    const result = await uploadFile(file);
    if (result.success && result.file_path) {
      // 启动检测
      startWithFile(result.file_path);
    }
  };
  ```

### 5. 操作顺序优化
- **修改文件**: `src/components/Detection.vue`
- **修改内容**: 将清空文件输入框的操作移到了删除文件之后，避免在等待后端释放资源的过程中清空用户选择的新文件。
- **业务逻辑**: 当用户点击停止检测时，系统先断开连接，等待后端释放资源，删除文件，最后再清空文件输入框，确保用户在等待过程中选择的新文件不会被清空。
- **伪代码**:
  ```javascript
  const stop = async () => {
    disconnect();
    isLoading.value = false;
    
    // 等待后端释放文件资源
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // 删除上传的文件
    if (currentFileName.value) {
      await deleteFile(currentFileName.value);
      currentFileName.value = '';
    }
    
    // 清空文件输入框，允许再次选择同一文件
    if (fileInputRef.value) {
      fileInputRef.value.value = '';
    }
  };
  ```

### 6. 状态管理初始化修复
- **修改文件**: `src/components/Detection.vue`
- **修改内容**: 修复了barnStore的初始化错误，将usePenStore()改为useBarnStore()。
- **业务逻辑**: 确保正确初始化状态管理对象，避免调用不存在的方法导致加载失败，确保养殖舍列表能够正常加载。
- **伪代码**:
  ```javascript
  // 修复前
  const barnStore = usePenStore(); // 错误：使用了错误的store
  const penStore = usePenStore();
  
  // 修复后
  const barnStore = useBarnStore(); // 正确：使用了正确的store
  const penStore = usePenStore();
  ```

### 7. 并发处理优化
- **修改文件**: `src/components/Detection.vue`
- **修改内容**: 将文件上传处理改为非阻塞方式，使用Promise的.then()方法处理文件上传，避免阻塞事件循环。
- **业务逻辑**: 当用户选择文件时，系统会异步上传文件，不会阻塞其他操作，支持多个页面同时上传文件和启动检测。
- **伪代码**:
  ```javascript
  // 修改前
  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    const result = await uploadFile(file);
    if (result.success && result.file_path) {
      startWithFile(result.file_path);
    }
  };
  
  // 修改后
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    // 非阻塞方式处理文件上传
    uploadFile(file).then(result => {
      if (result.success && result.file_path) {
        startWithFile(result.file_path);
      }
    }).catch(error => {
      log(`文件上传失败: ${error.message}`, 'error');
    });
  };
  ```

### 8. WebSocket连接优化
- **修改文件**: `src/composables/useWebSocket.ts`
- **修改内容**: 修复了URL编码问题，确保WebSocket连接能够正确建立。
- **业务逻辑**: 当用户选择文件后，系统会正确构建WebSocket连接URL，确保连接能够成功建立，避免因URL编码错误导致的连接失败。
- **伪代码**:
  ```javascript
  // 修改前
  const encodedValue = encodeURIComponent(value);
  const qs = new URLSearchParams();
  qs.set('kind', kind);
  if (encodedValue) qs.set('value', decodeURIComponent(encodedValue));
  
  // 修改后
  const qs = new URLSearchParams();
  qs.set('kind', kind);
  if (value) qs.set('value', value);
  ```

### 9. 后端并发处理优化
- **修改文件**: `modules/websocket_manager.py`
- **修改内容**: 将同步的帧编码操作改为异步操作，使用asyncio.run_in_executor()在后台线程中执行编码操作，避免阻塞事件循环。
- **业务逻辑**: 当多个WebSocket连接同时发送帧数据时，系统会异步处理编码操作，不会阻塞事件循环，支持多个连接同时处理。
- **伪代码**:
  ```python
  # 修改前
  ok, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, C.JPEG_QUALITY])
  if not ok:
      raise RuntimeError("Failed to encode frame to JPEG")
  frame_data = base64.b64encode(buffer).decode('utf-8')
  
  # 修改后
  loop = asyncio.get_event_loop()
  def encode_frame():
      ok, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, C.JPEG_QUALITY])
      if not ok:
          raise RuntimeError("Failed to encode frame to JPEG")
      return base64.b64encode(buffer).decode('utf-8')
  
  frame_data = await loop.run_in_executor(None, encode_frame)
  ```

### 10. 后端WebSocket处理优化
- **修改文件**: `modules/main.py`
- **修改内容**: 优化了WebSocket处理逻辑，使用非阻塞方式获取帧数据，避免阻塞事件循环。
- **业务逻辑**: 当多个WebSocket连接同时处理时，系统会非阻塞地获取帧数据，不会阻塞事件循环，支持多个连接同时处理。
- **伪代码**:
  ```python
  # 修改前
  frame = result_queue.get(timeout=1.0)
  
  # 修改后
  try:
      frame = result_queue.get(block=False)
  except queue.Empty:
      await asyncio.sleep(0.01)
      continue
  ```

### 11. 后端检测器实例管理
- **修改文件**: `modules/main.py`
- **修改内容**: 为每个WebSocket连接创建独立的检测器实例，避免共享检测器导致的并发冲突。
- **业务逻辑**: 当多个连接同时进行检测时，每个连接都会使用自己的检测器实例，避免共享检测器导致的并发冲突，确保检测结果的准确性。
- **伪代码**:
  ```python
  def get_detector():
      """为每个连接创建一个新的检测器实例"""
      detector = PTDetector(C.PT_MODEL_PATH)
      print("Detector initialized successfully for new connection", flush=True)
      return detector
  
  # 在WebSocket处理函数中
  det = get_detector()
  ```

## 启动项目

### 前端开发服务器
```bash
cd vue-frontend
npm run dev
```

### 后端服务器
```bash
# 在项目根目录运行
python -m modules.main
```

## 访问地址

- 前端: http://localhost:5173
- 后端API: http://localhost:8080

## 功能说明

- **本地文件检测**: 支持上传本地图片和视频进行检测
- **摄像头检测**: 支持连接养殖场摄像头进行实时检测
- **实时画面显示**: 通过WebSocket接收后端处理的帧数据并显示
- **事件记录**: 当检测到mating事件时，会记录到事件表中
- **文件管理**: 点击停止检测后会自动删除上传的文件，避免数据堆积

## 注意事项

- 确保后端服务器正在运行，否则前端无法连接
- 上传的文件会保存在`uploads`目录中，检测完成后会自动删除
- 对于大文件，检测可能需要较长时间，请耐心等待
- 如果遇到文件删除失败的情况，可能是后端资源未完全释放，请稍后再试
