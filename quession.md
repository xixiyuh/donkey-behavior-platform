你是一个资深 Python 后端工程师和实时视频流架构工程师，请直接修改我的整个项目代码，实现下面这个目标：

# 目标

把当前项目从“**每个 WebSocket 连接独立创建 stream + reader/infer pipeline**”改造成“**同一个视频源共享一整套 reader/infer pipeline，多连接只做结果订阅**”的架构。

也就是说：

- 相同的视频源（例如相同 FLV/RTSP URL，或相同 camera_id）只能存在 **一个共享 SourceSession**

- 一个 

  ```
  SourceSession
  ```

   只允许有：

  - **1 套 reader**
  - **1 套 infer**
  - **1 份共享最新帧/结果**

- 多个 WebSocket 连接访问同一路视频时：

  - 不再重复 `open_source`
  - 不再重复启动 `start_pipeline`
  - 不再重复进行模型推理
  - 只作为订阅者接收同一个 session 广播出来的结果

- 当最后一个订阅者断开后：

  - 不要立刻销毁，支持一个可配置的空闲 TTL（例如 60 秒）
  - TTL 到期后再停止线程、关闭流、释放 session

------

# 当前项目背景

项目是一个 FastAPI + WebSocket 的实时视频检测系统。
 目前的问题是：

- 每个 `/ws` 连接都会独立 `open_source(...)`
- 每个连接都会独立调用 `start_pipeline(...)`
- 即使多个用户访问同一路视频，也会重复拉流、重复解码、重复推理
- 这会造成线程数线性增长、网络带宽浪费、推理资源浪费

我已经做过一个 `stream_manager.py`，它只能共享“裸 stream 实例”，但这还不够。
 **你现在要做的是：共享整套 pipeline，而不是只共享 stream。**

------

# 必须实现的架构

请新增并集成一个类似下面职责的模块（名字你可以调整，但职责必须满足）：

## 1. SourceSession

表示一个共享视频源会话，至少包含：

- `source_key`
- `stream`
- `subscribers`
- `ref_count`
- `stop_event`
- `reader_thread`
- `infer_thread`
- `latest_frame`
- `latest_result`
- `last_active_time`
- 必要的锁（threading.Lock / RLock / asyncio.Lock）

职责：

- 打开和持有视频流
- 启动并管理 reader/infer
- 保存最新帧和最新检测结果
- 向多个 websocket 广播结果
- 管理订阅者增删
- 管理空闲超时和资源释放

## 2. SourceManager / SessionManager

全局注册中心，维护：

- `source_key -> SourceSession`

职责：

- 根据 `kind + value (+ camera_id)` 生成唯一 `source_key`
- `get_or_create_session(...)`
- `acquire(...)`
- `release(...)`
- 空闲 TTL 清理
- `close_all()`
- `get_stats()` 供接口查看

------

# 关键行为要求

## 1. 同源只允许一套 pipeline

对于相同视频源：

- 只能 `open_source(...)` 一次
- 只能启动一套 reader/infer
- 多个 websocket 连接不得重复创建后台线程
- 多个 websocket 只能共享结果

## 2. WebSocket 只负责订阅

请把现在 `main.py` 中 `/ws` 路由逻辑改掉：

旧逻辑大概是：

- accept
- open_source
- start_pipeline
- 当前连接独占结果

新逻辑必须变成：

- accept
- 根据参数构建 `source_key`
- 从 `SourceManager` 获取或创建共享 `SourceSession`
- 把当前 websocket 注册成该 session 的 subscriber
- websocket 不再自己创建 stream 和 pipeline
- websocket 只负责：
  - 保持连接
  - 接收 session 广播出来的结果
  - 断开时取消订阅

## 3. reader 线程职责

reader 线程负责：

- 独占读取共享 stream
- 持续读取最新帧
- 只保留最新帧，不要让帧积压
- 如有必要，可以使用 `queue.Queue(maxsize=1)`，或者直接维护 `latest_frame`
- 保证不会出现多个线程并发读取同一个 stream

## 4. infer 线程职责

infer 线程负责：

- 只从共享 `latest_frame` 或共享帧队列中获取数据
- 只对同一路视频执行一次推理
- 更新 `latest_result`
- 将结果广播给所有订阅者
- 不允许每个 websocket 自己重复推理

## 5. 广播机制

必须实现安全的多订阅者广播：

- 推理线程产生结果后，广播给所有订阅 websocket
- 由于 websocket 是 async 的，而 reader/infer 可能是线程，请正确处理线程与 asyncio 事件循环的边界
- 推荐使用：
  - `asyncio.run_coroutine_threadsafe(...)`
  - 或者为每个订阅者维护异步发送队列
- 发送失败的 websocket 要自动移除，避免死连接堆积

## 6. 引用计数与释放

必须支持：

- 新连接订阅：`ref_count + 1`

- 连接断开：`ref_count - 1`

- 当 

  ```
  ref_count == 0
  ```

   时：

  - 不立即销毁
  - 记录 `last_active_time`
  - 后台 cleanup 线程/协程定时回收空闲 session

- 真正销毁时必须按正确顺序：

  1. 先通知 reader/infer 停止
  2. 等线程退出
  3. 再关闭 stream
  4. 再从 manager 中移除

## 7. 必须避免的错误

请特别避免以下问题：

- 多个线程同时 `read()` 同一个 stream
- 多个 websocket 重复触发模型推理
- 全局共用一个 `stop_event` 导致停一个源时全体停掉
- 全局共用一个混杂的 `result_queue` 导致不同 source 的结果串流
- websocket 已断开但还保留在 subscribers 中
- session 已释放，但后台线程还在读流或推理
- close 顺序错误导致后台线程访问已关闭的 stream
- 锁粒度错误导致死锁或严重阻塞

------

# 代码改造要求

请你直接改项目代码，不要只给思路。

要求你：

1. 扫描并理解整个项目中与以下内容相关的代码：
   - `main.py`
   - `open_source`
   - `start_pipeline`
   - `result_queue`
   - WebSocket 管理
   - 检测器 `det`
   - stop_event / threads / stream 生命周期
2. 找出当前“每连接独立 pipeline”的实现位置
3. 进行完整重构
4. 给出修改后的关键文件完整代码
5. 如果需要新增文件，请给出完整新增文件内容
6. 如果需要修改多个已有文件，请逐个输出改动后的完整版本
7. 不要只写伪代码，尽量给出可运行代码
8. 如果某些函数签名必须调整，请同步修改调用方
9. 保持项目原有业务能力不丢失：
   - camera_id / pen_id / barn_id 等元信息仍要保留
   - 原有检测逻辑尽量保持
   - 原有 WebSocket 对外接口尽量兼容
10. 如果项目里已有 `stream_manager.py`，请判断它是否保留、替换还是升级；不要保留“共享裸 stream 但不共享 pipeline”的危险设计

------

# 输出格式要求

请按下面格式输出：

## 第一步：先分析当前问题

- 指出项目中哪些位置导致了“每连接独立 pipeline”
- 指出当前 `stream_manager.py` 方案为什么不完整
- 指出哪些共享对象存在并发安全风险

## 第二步：给出重构方案

- 给出新的类设计
- 给出生命周期设计
- 给出线程/async 边界设计

## 第三步：直接给代码

按文件输出完整代码，例如：

- `modules/source_manager.py`
- `modules/main.py`
- 其他被修改的文件

要求尽量给完整文件，不要只给零碎 diff。

## 第四步：说明如何验证

至少给出下面验证方式：

- 3 个用户连接同一路视频时，只创建 1 个 session
- 只启动 1 套 reader/infer
- 引用计数正确增减
- 最后一个连接断开后，TTL 到期才释放
- `/stream-stats` 或类似接口能看到 session 状态
- 日志里能证明同一路视频只推理一次，多连接只是共享订阅

## 第五步：指出兼容性与风险

- 如果 detector `det` 不是线程安全的，该怎么保护
- 如果某些 source 类型不支持复用，要怎么处理
- 如果广播过慢，要怎么优化

------

# 额外要求

- 优先在现有项目结构上做最小必要改造，但架构必须正确
- 代码要有必要注释
- 不要为了省事保留“每连接一套 pipeline”的旧逻辑
- 不要只共享流对象，必须共享整套 reader/infer pipeline
- 不要只讲理论，必须交付具体代码
- 如果你认为某个旧模块应该删除或废弃，请明确说明
- 如果发现项目中某些函数设计不适合共享架构，可以合理重构，但要说明原因
- 请尽量保证代码风格统一，命名清晰，可维护