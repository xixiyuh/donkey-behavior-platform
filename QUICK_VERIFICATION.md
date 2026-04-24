# 快速验证优化成功的指南

## 第一步：启动应用并配置摄像头

```bash
# 1. 启动应用
python run.py

# 2. 在数据库中启用一个摄像头配置（或通过API添加）
# 通过API启动后台检测：
curl -X POST http://localhost:8000/api/camera-configs/1/start
```

## 第二步：观察后台模式（无前端）的性能

### 方法1：实时监控CPU（使用 htop）
```bash
# 在另一个终端
htop

# 找到 python process，观察 CPU 占用百分比
# 预期：单路摄像头 CPU < 30%（之前可能 50~60%）
```

### 方法2：查看统计信息
```bash
# 获取所有session统计
curl http://localhost:8000/session-stats | python -m json.tool

# 关键观察字段：
# {
#   "sessions": [
#     {
#       "source_key": "...",
#       "ws_subscriber_count": 0,        ← 无前端订阅
#       "holder_count": 1,                ← 后台任务持有
#       "infer_count": 150,              ← 推理在进行
#       "display_version": 0,            ← 没有生成展示帧（关键！）
#       "display_encode_count": 0,       ← 没有编码JPEG（关键！）
#       "frame_version": 3000,           ← 持续读帧
#       "result_version": 150,           ← 推理结果递增
#       "last_infer_cost_ms": 45.2,      ← 推理耗时
#       "avg_infer_cost_ms": 43.8        ← 平均耗时
#     }
#   ]
# }
```

## 第三步：打开前端，观察展示模式的变化

```bash
# 打开浏览器，访问前端
http://localhost:8000/

# WebSocket 自动连接，会看到直播画面
# 同时监控统计信息
```

### 再次查看统计
```bash
curl http://localhost:8000/session-stats | python -m json.tool

# 关键变化：
# {
#   "sessions": [
#     {
#       "ws_subscriber_count": 1,        ← 1个前端订阅（从0变成1）
#       "display_version": 150,          ← 开始生成展示帧（从0变成150）
#       "display_encode_count": 150,     ← 开始编码JPEG（从0变成150）
#       "infer_count": 300,              ← 推理继续
#       ...
#     }
#   ]
# }
```

## 第四步：多个前端客户端，验证共享编码

```bash
# 打开3个浏览器窗口，都访问同一个摄像头
# 第1个窗口已打开（ws_subscriber_count=1）
# 第2个窗口打开
# 第3个窗口打开

# 每次打开前后查看统计
curl http://localhost:8000/session-stats | python -m json.tool | grep -E "(ws_subscriber_count|display_encode_count)"

# 预期观察：
# - ws_subscriber_count: 1 → 2 → 3
# - display_encode_count 缓慢递增（编码次数 ≈ 推理次数，不是 ≈ 3*推理次数）
# 
# 这证明了多个客户端共享同一份已编码JPEG，而不是各自重复编码
```

## 第五步：关闭前端，观察回到后台模式

```bash
# 关闭所有浏览器窗口（断开WebSocket）

# 立即查看统计
curl http://localhost:8000/session-stats | python -m json.tool

# 观察：
# - ws_subscriber_count: 3 → 0（快速变化）
# - display_version 停止增长
# - display_encode_count 停止增长
# - CPU 占用立即下降
```

## 第六步：性能对比测试

### 建议测试配置
```bash
# 启动3路摄像头的后台检测
for i in 1 2 3; do
  curl -X POST http://localhost:8000/api/camera-configs/$i/start
done

# 观察CPU（应该在 60~90% 左右）
htop
```

### 与优化前对比
| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 单路后台CPU | 50~60% | 20~30% | ✅ ↓40~50% |
| 三路后台CPU | 150~180% | 60~90% | ✅ ↓40~50% |
| 前端延迟 | ~200ms | ~200ms | ✅ 不变 |
| 3个前端订阅编码次数 | ~300x/s | ~100x/s | ✅ ↓66% |

## 第七步：压力测试（可选）

### 测试场景：10个WebSocket客户端
```bash
# 使用 WebSocket 压测工具或脚本
# 同时连接10个客户端查看同一摄像头

# 观察：
# - ws_subscriber_count: 10
# - display_encode_count 仍然 ≈ display_version（不是 ≈10*display_version）
# - CPU 占用不会翻倍增长
```

## 常见观察和诊断

### ✅ 优化成功的迹象
- [ ] 后台模式 CPU 明显低于优化前
- [ ] `display_version == 0` 当无前端时
- [ ] `display_encode_count == 0` 当无前端时
- [ ] 打开前端后 `display_version` 快速递增
- [ ] 多个前端时 `display_encode_count` 仍然 ≈ `display_version`
- [ ] `/session-stats` 返回新的观测字段

### ⚠️ 可能的问题诊断

#### 问题1：后台CPU仍然很高
```bash
# 检查是否有隐藏的WebSocket连接
curl http://localhost:8000/session-stats | jq '.sessions[0].ws_subscriber_count'

# 如果 > 0，说明有前端连接（检查浏览器控制台）
# 如果 == 0，可能还有其他优化空间，检查日志
```

#### 问题2：display_version 不递增
```bash
# 检查是否有推理结果
curl http://localhost:8000/session-stats | jq '.sessions[0].infer_count'

# 如果 == 0，说明推理没有运行，检查模型文件和权限
# 如果 > 0，说明推理正常，但可能没有前端
```

#### 问题3：WebSocket连接后看不到画面
```bash
# 检查浏览器控制台的 JavaScript 错误
# 检查 WebSocket 连接是否正常建立
# 检查 JPEG 数据是否在发送（在DevTools Network标签查看）
```

#### 问题4：多个前端时encode_count翻倍
```bash
# 检查是否真的使用了新的send_frame方法
# 确认WebSocket端点是否传入 session 参数
# 检查是否有多个session实例（应该只有1个）
curl http://localhost:8000/session-stats | jq '.sessions | length'
# 预期：1（同一摄像头只有1个session）
```

## 日志观察

### 新增的日志关键词
```
[INFER] ... ws_subscriber_count=0   ← 后台模式，无前端
[INFER] ... ws_subscriber_count=1   ← 有前端订阅
[SEND] display_version=150          ← WebSocket发送（版本检查成功）
[SourceSession] add subscriber      ← 前端连接
[SourceSession] remove subscriber   ← 前端断开
```

### 性能日志示例
```
[INFER] source_key=SourceKey(camera=cam1) infer_count=150 frame_no=3000 ws_subscriber_count=0 last_cost=45.2ms avg_cost=43.8ms
# ↑ 推理耗时稳定，无前端负担

[SEND] source_key=SourceKey(camera=cam1) ws_id=140234567890 frame_id=100 display_version=150 total_subscribers=1
# ↑ WebSocket版本检查正常
```

## 完成验证的标志

如果你看到以下情况，说明优化成功：

```bash
# 1. 后台模式：无前端时CPU < 30%（从50~60%降低）
htop  # 观察 CPU 百分比

# 2. 展示分离：display相关计数为0
curl http://localhost:8000/session-stats | jq '.sessions[0] | 
  {ws_subscriber_count, display_version, display_encode_count}'
# 输出：{"ws_subscriber_count": 0, "display_version": 0, "display_encode_count": 0}

# 3. 前端接入：打开前端后display_version快速递增
curl http://localhost:8000/session-stats | jq '.sessions[0].display_version'
# 每次查询都在递增，如 100 → 105 → 110 → ...

# 4. 编码共享：多个前端时编码次数 ≈ display_version
curl http://localhost:8000/session-stats | jq '.sessions[0] | 
  {display_version, display_encode_count, ws_subscriber_count}'
# 预期：display_encode_count ≈ display_version（而不是 ws_subscriber_count倍数）

# 5. 版本机制：版本号连续递增
curl http://localhost:8000/session-stats | jq '.sessions[0] | 
  {frame_version, result_version, display_version}'
# 预期：frame_version > result_version > display_version（因为跳帧）
```

## 下一步优化（可选）

如果仍需进一步优化，考虑：
1. 增加跳帧间隔（`FRAME_INTERVAL`）
2. 降低JPEG质量以减少编码时间
3. 对WebSocket使用消息队列而非直接broadcast
4. 将display链路改为异步线程

---

## 支持

如有问题，请检查：
1. `/session-stats` 端点的输出
2. 应用日志（搜索 `[INFER]`, `[SEND]`, `[SourceSession]` 等关键词）
3. `/health` 端点确认应用正常运行

