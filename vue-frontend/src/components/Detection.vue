<template>
  <div class="detection-container">
    <h2>实时检测</h2>

    <div class="info-panel">
      <small>
        <strong>支持输入源：</strong> 本地视频 | 本地图片<br>
        <strong>AI模型：</strong> YOLOv8 + 对比学习交配行为识别<br>

      </small>
    </div>

    <div class="row" style="margin-bottom: 16px;">
      <div>
        <label for="barn">养殖舍</label>
        <select
          id="barn"
          v-model="selectedBarn"
          @change="loadPens"   <!-- 选完牛舍,自动加载该牛舍下的栏位 -->
        >
          <option value="">请选择养殖舍</option>
          <option
            v-for="barn in barns"
            :key="barn.id"
            :value="barn.id"
          >
            {{ barn.name }} ({{ barn.total_pens }}栏)
          </option>
        </select>
      </div>
      <div>
        <label for="pen">栏</label>
        <select
          id="pen"
          v-model="selectedPen"
          @change="loadCameras"
        >
          <option value="">请选择栏</option>
          <option
            v-for="pen in pens"
            :key="pen.id"
            :value="pen.id"
          >
            第{{ pen.pen_number }}栏
          </option>
        </select>
      </div>
      <div>
        <label for="camera">摄像头</label>
        <select
          id="camera"
          v-model="selectedCamera"
        >
          <option value="">请选择摄像头</option>
          <option
            v-for="camera in cameras"
            :key="camera.id"
            :value="camera.flv_url"
          >
            {{ camera.camera_id }}
          </option>
        </select>
      </div>
    </div>

    <div class="row">
      <div style="display: flex; gap: 10px; align-items: end;">
        <div style="flex: 1;">
          <label>输入源类型</label>
          <div class="input-source-text">本地图片/视频</div>
        </div>
        <div style="align-self: end;">
          <input
            ref="fileInputRef"
            type="file"
            id="fileInput"
            style="display: none;"
            accept="video/*,image/*"
            @change="handleFileSelect"
          />
          <button @click="triggerFileSelect" title="选择文件">📁</button>
        </div>
      </div>

      <div class="buttons">
        <button
          id="btnStart"
          @click="start"
          :disabled="isConnected"
        >
          🟢 开始
        </button>
        <button
          id="btnStop"
          @click="stop"
          :disabled="!isConnected"
        >
          🔴 停止
        </button>
        <button id="btnHealth" @click="checkHealth">❤️ 健康检查</button>
      </div>
    </div>

    <label style="margin-top:16px;">实时画面</label>
    <div class="preview">
      <img
        v-if="frame && !isLoading"
        :src="`data:image/jpeg;base64,${frame}`"
        alt="实时画面"
      />
      <div v-else-if="isLoading" class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">正在加载视频源...</div>
      </div>
      <div v-else class="placeholder">
        <div style="font-size: 48px; margin-bottom: 10px;">📹</div>
        <div>等待连接视频源...</div>
      </div>
      <div
        :class="['status', isConnected ? 'connected' : 'disconnected']"
      >
        {{ isConnected ? '已连接' : '未连接' }}
      </div>
    </div>

    <label style="margin-top:16px;">系统日志</label>
    <div class="log" ref="logContainer">
      <div v-for="(log, index) in logs" :key="index" :class="log.type">
        [{{ log.time }}] {{ log.prefix }} {{ log.message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
 ref, onMounted, watch } from 'vue';
import { useBarnStore } from '../stores/barn';
import { usePenStore } from '../stores/pen';
import { useWebSocket } from '../composables/useWebSocket';
import { useApi } from '../composables/useApi';
import type { Barn, Pen, Camera } from '../types';

// 状态
const barnStore = useBarnStore();
const penStore = usePenStore();
const { isConnected, frame, connect, disconnect } = useWebSocket();
const { uploadFile, deleteFile, checkHealth: checkSystemHealth } = useApi();

const barns = ref<Barn[]>([]);
const pens = ref<Pen[]>([]);
const cameras = ref<Camera[]>([]);
const selectedBarn = ref<string>('');//创建一个【响应式字符串变量】用来存【当前选中的牛舍ID】一开始是空
const selectedPen = ref<string>('');
const selectedCamera = ref<string>('');
const kind = ref<string>('file');
const logs = ref<Array<{ time: string; prefix: string; message: string; type: string }>>([]);
const logContainer = ref<HTMLElement | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const currentFileName = ref<string>('');
const isLoading = ref<boolean>(false);

// 日志函数
const log = (message: string, type: 'info' | 'error' | 'success' = 'info') => {
  const now = new Date().toLocaleTimeString();
  const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
  logs.value.push({ time: now, prefix, message, type });

  // 滚动到底部
  setTimeout(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    }
  }, 100);
};

// 加载养殖舍列表
const loadBarns = async () => {
  try {
    await barnStore.fetchBarns();
    barns.value = barnStore.allBarns;
    log('养殖舍列表加载成功', 'success');
  } catch (error) {
    log('加载养殖舍列表失败', 'error');
  }
};

// 加载所有摄像头
const loadAllCameras = async () => {
  try {
    // 从penStore获取所有摄像头
    await penStore.fetchPens();
    const allPens = penStore.allPens;
    const allCameraPromises = allPens.map(pen => penStore.fetchPenCameras(pen.id));
    const cameraLists = await Promise.all(allCameraPromises);
    // 合并所有摄像头列表
    const allCameras = cameraLists.flat();
    // 去重
    const uniqueCameras = Array.from(new Map(allCameras.map(camera => [camera.id, camera])).values());
    cameras.value = uniqueCameras;
    selectedCamera.value = '';
    log('所有摄像头加载成功', 'success');
  } catch (error) {
    log('加载所有摄像头失败', 'error');
  }
};

// 加载栏列表
const loadPens = async () => {
  if (!selectedBarn.value) {
    pens.value = [];
    await loadAllCameras();
    selectedPen.value = '';
    selectedCamera.value = '';
    return;
  }

  try {
    const penList = await barnStore.fetchBarnPens(Number(selectedBarn.value));
    pens.value = penList;
    // 加载该养殖舍的所有摄像头
    const cameraPromises = penList.map((pen: Pen) => penStore.fetchPenCameras(pen.id));
    const cameraLists = await Promise.all(cameraPromises);
    const barnCameras = cameraLists.flat();
    const uniqueCameras = Array.from(new Map(barnCameras.map(camera => [camera.id, camera])).values());
    cameras.value = uniqueCameras;
    selectedPen.value = '';
    selectedCamera.value = '';
    log('栏列表加载成功', 'success');
  } catch (error) {
    log('加载栏列表失败', 'error');
  }
};

// 加载摄像头列表
const loadCameras = async () => {
  if (!selectedPen.value) {
    // 如果没有选择栏,加载该养殖舍的所有摄像头
    if (selectedBarn.value) {
      try {
        const penList = await barnStore.fetchBarnPens(Number(selectedBarn.value));
        const cameraPromises = penList.map((pen: Pen) => penStore.fetchPenCameras(pen.id));
        const cameraLists = await Promise.all(cameraPromises);
        const barnCameras = cameraLists.flat();
        const uniqueCameras = Array.from(new Map(barnCameras.map(camera => [camera.id, camera])).values());
        cameras.value = uniqueCameras;
      } catch (error) {
        log('加载养殖舍摄像头失败', 'error');
      }
    } else {
      // 如果没有选择养殖舍,加载所有摄像头
      await loadAllCameras();
    }
    selectedCamera.value = '';
    return;
  }

  try {
    const cameraList = await penStore.fetchPenCameras(Number(selectedPen.value));
    cameras.value = cameraList;
    selectedCamera.value = '';
    log('摄像头列表加载成功', 'success');
  } catch (error) {
    log('加载摄像头列表失败', 'error');
  }
};

// 触发文件选择
const triggerFileSelect = () => {
  fileInputRef.value?.click();
};

// 文件选择处理
const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    log(`文件信息: ${file.name} (${file.size} bytes, ${file.type})`, 'info');

    // 先断开现有连接,避免冲突
    if (isConnected.value) {
      log('断开现有连接以处理新文件', 'info');
      disconnect();
      isLoading.value = false;
    }

    // 上传文件（非阻塞）
    uploadFile(file).then(result => {
      if (result.success && result.file_path) {
        log(`文件上传成功,路径: ${result.file_path}`, 'success');

        // 保存当前文件名,用于后续删除
        currentFileName.value = file.name;
        log(`已记录文件名: ${file.name}`, 'info');

        // 根据文件类型设置kind
        if (file.type.startsWith('image/')) {
          kind.value = 'image';
          log('设置kind为: image', 'info');
        } else if (file.type.startsWith('video/')) {
          kind.value = 'file';
          log('设置kind为: file', 'info');
        }

        // 启动检测
        startWithFile(result.file_path);
      } else {
        log(`文件上传失败: ${result.message}`, 'error');
      }
    }).catch(error => {
      log(`文件上传失败: ${error instanceof Error ? error.message : '未知错误'}`, 'error');
    });
  }
};

// 带文件路径的启动函数
const startWithFile = (filePath: string) => {
  log(`当前kind: ${kind.value}`, 'info');
  log(`当前value: ${filePath}`, 'info');
  log(`当前barn_id: ${selectedBarn.value}`, 'info');
  log(`当前pen_id: ${selectedPen.value}`, 'info');

  if (!filePath) {
    log('请选择文件或摄像头', 'error');
    return;
  }

  log(`正在连接: ${kind.value} - ${filePath}`, 'info');
  isLoading.value = true;
  // 关键修复：file/video/image 类型不传 camera_id，否则会复用旧的 session！！！
  // 让每个文件都创建自己独立的 session！
  connect(kind.value, filePath, undefined, selectedPen.value ? Number(selectedPen.value) : undefined, selectedBarn.value ? Number(selectedBarn.value) : undefined);
  // 假设连接成功后会设置isConnected为true,我们监听这个变化来关闭加载状态
  setTimeout(() => {
    if (!isConnected.value) {
      isLoading.value = false;
    }
  }, 5000); // 5秒后如果还没连接成功,自动关闭加载状态
};

// 启动函数
const start = () => {
  let value = '';
  let cameraId = ''; // 摄像头的真实ID

  // 如果选择了摄像头,则使用摄像头的FLV地址
  if (selectedCamera.value) {
    value = selectedCamera.value;

    // 从摄像头列表中找到对应的camera对象,获取真实的camera_id
    const selectedCameraObj = cameras.value.find(cam => cam.flv_url === value);
    cameraId = selectedCameraObj?.camera_id || value; // 优先使用真实camera_id,否则使用URL

    kind.value = 'flv'; // 使用FLV格式，与后台检测共享同一套pipeline
    log(`使用摄像头地址: ${value}`, 'info');
    log(`使用摄像头ID: ${cameraId}`, 'info');
  } else {
    log('请选择文件或摄像头', 'error');
    return;
  }

  log(`当前kind: ${kind.value}`, 'info');
  log(`当前value: ${value}`, 'info');
  log(`当前barn_id: ${selectedBarn.value}`, 'info');
  log(`当前pen_id: ${selectedPen.value}`, 'info');

  if (!value) {
    log('请选择文件或摄像头', 'error');
    return;
  }

  log(`正在连接: ${kind.value} - ${value}`, 'info');
  isLoading.value = true;
  connect(kind.value, value, cameraId, selectedPen.value ? Number(selectedPen.value) : undefined, selectedBarn.value ? Number(selectedBarn.value) : undefined);
  // 假设连接成功后会设置isConnected为true,我们监听这个变化来关闭加载状态
  setTimeout(() => {
    if (!isConnected.value) {
      isLoading.value = false;
    }
  }, 5000); // 5秒后如果还没连接成功,自动关闭加载状态
};

// 停止函数
const stop = async () => {
  disconnect();
  isLoading.value = false;
  log('已停止连接', 'info');

  // 清空当前文件名，不再立即删除文件（文件会在每天固定时间统一清理）
  currentFileName.value = '';

  // 清空文件输入框,允许再次选择同一文件
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
};

// 健康检查
const checkHealth = async () => {
  try {
    const result = await checkSystemHealth();
    if (result && result.status === 'ok') {
      log('系统健康检查通过 ✅', 'success');
    } else {
      log('系统健康检查失败', 'error');
    }
  } catch (error) {
    log('健康检查请求失败', 'error');
  }
};

// 监听连接状态变化,当连接状态改变时重置加载状态
watch(isConnected, () => {
  // 无论是连接成功还是关闭,都关闭加载状态
  isLoading.value = false;
});

// 组件挂载时加载数据
onMounted(async () => {
  log('页面完全加载完成', 'success');
  log('RK3588 实时检测系统已就绪', 'success');
  await loadBarns();
  await loadAllCameras();
});
</script>

<style scoped>
.detection-container {
  width: 100%;
}

.info-panel {
  background: #1a2332;
  border-radius: 8px;
  padding: 10px;
  margin-top: 10px;
  border-left: 3px solid #60a5fa;
  margin-bottom: 20px;
}

.row {
  display: grid;
  grid-template-columns: 1fr 2fr auto;
  gap: 12px;
  align-items: end;
  margin-bottom: 16px;
}

label {
  font-size: 14px;
  color: #b9c2d0;
  display: block;
  margin: 8px 0 4px;
}

input, select, .input-source-text {
  width: 100%;
  padding: 10px;
  border-radius: 10px;
  border: 1px solid #334;
  background: #172045;
  color: #e7e9ee;
  box-sizing: border-box;
}

.buttons {
  display: flex;
  gap: 12px;
}

button {
  cursor: pointer;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid #345;
  background: #1d2a5a;
  color: #e7e9ee;
  transition: background 0.2s;
}

button:hover {
  background: #26346e;
}

button:disabled {
  background: #666;
  cursor: not-allowed;
}

.preview {
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #243;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 360px;
  position: relative;
  margin-bottom: 20px;
}

.preview img {
  width: 100%;
  height: auto;
  display: block;
}

.placeholder {
  color: #666;
  text-align: center;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #60a5fa;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  color: #b9c2d0;
  font-size: 16px;
  text-align: center;
}

.status {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 5px 10px;
  border-radius: 5px;
  font-size: 12px;
}

.status.connected {
  background: #065f46;
  color: #d1fae5;
}

.status.disconnected {
  background: #7f1d1d;
  color: #fecaca;
}

.log {
  white-space: pre-wrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: #0f1533;
  padding: 10px;
  border-radius: 10px;
  height: 120px;
  overflow: auto;
  border: 1px solid #223;
  font-size: 12px;
}

.log div {
  margin-bottom: 4px;
}

.log div.error {
  color: #fecaca;
}

.log div.success {
  color: #d1fae5;
}

.log div.info {
  color: #e7e9ee;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .row {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .buttons {
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .preview {
    min-height: 240px;
  }

  .log {
    height: 100px;
  }
}
</style>
