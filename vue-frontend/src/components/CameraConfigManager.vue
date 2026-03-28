<template>
  <div class="camera-config-manager">
    <h2>摄像头检测配置</h2>

    <!-- 摄像头配置表单 -->
    <div class="form">
      <div class="form-row">
        <div class="form-group half">
          <label>养殖舍</label>
          <select v-model="newCamera.barn_id" @change="handleBarnChange">
            <option value="" disabled selected style="color: #888;">请选择养殖舍</option>
            <option v-for="barn in barns" :key="barn.id" :value="barn.id">
              {{ barn.name }}
            </option>
          </select>
        </div>
        <div class="form-group half">
          <label>栏</label>
          <select v-model="newCamera.pen_id" @change="handlePenChange">
            <option value="" disabled selected style="color: #888;">请选择栏</option>
            <option v-for="pen in pens" :key="pen.id" :value="pen.id">
              第{{ pen.pen_number }}栏
            </option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label>摄像头</label>
        <select v-model="selectedCameraId" @change="handleCameraChange">
          <option value="" disabled selected style="color: #888;">请选择摄像头</option>
          <option v-for="camera in filteredCameras" :key="camera.id" :value="camera.id">
            {{ camera.camera_id }}
          </option>
        </select>
      </div>
      <div class="form-group">
        <label>摄像头ID</label>
        <input v-model="newCamera.camera_id" type="text" placeholder="摄像头ID" readonly>
      </div>
      <div class="form-group">
        <label>FLV地址</label>
        <input v-model="newCamera.flv_url" type="text" placeholder="FLV地址" readonly>
      </div>
      <div class="form-row">
        <div class="form-group half">
          <label>开始时间</label>
          <input v-model="newCamera.start_time" type="time" placeholder="开始时间">
        </div>
        <div class="form-group half">
          <label>结束时间</label>
          <input v-model="newCamera.end_time" type="time" placeholder="结束时间">
        </div>
      </div>
      <button @click="addCamera">添加摄像头配置</button>
    </div>

    <!-- 摄像头配置列表 -->
    <div class="camera-list">
      <h3>已配置摄像头</h3>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>摄像头ID</th>
            <th>FLV地址</th>
            <th>养殖舍</th>
            <th>栏</th>
            <th>检测时间</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="camera in cameraConfigs" :key="camera.id">
            <td>{{ camera.id }}</td>
            <td>{{ camera.camera_id }}</td>
            <td>{{ camera.flv_url }}</td>
            <td>{{ getBarnName(camera.barn_id) }}</td>
            <td>{{ camera.pen_id }}</td>
            <td>{{ camera.start_time }} - {{ camera.end_time }}</td>
            <td>{{ camera.enable ? '启用' : '禁用' }}</td>
            <td>
              <button @click="toggleCamera(camera.id)">
                {{ camera.enable ? '禁用' : '启用' }}
              </button>
              <button @click="deleteCamera(camera.id)">删除</button>
            </td>
          </tr>
          <tr v-if="(cameraConfigs || []).length === 0">
            <td colspan="8" style="text-align: center;">暂无摄像头配置</td>
          </tr>
        </tbody>
      </table>
      <!-- 分页控件 -->
      <div class="pagination">
        <button @click="changePage(1)" :disabled="currentPage === 1">首页</button>
        <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1">上一页</button>
        <span>{{ currentPage }} / {{ totalPages }}</span>
        <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages">下一页</button>
        <div class="page-jump">
          <input type="number" v-model.number="jumpPage" min="1" :max="totalPages" style="width: 60px; margin: 0 10px;" />
          <button @click="jumpToPage">跳转</button>
        </div>
        <span class="total-records">共 {{ cameraStore.configTotal }} 条记录</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useBarnStore } from '../stores/barn';
import { usePenStore } from '../stores/pen';
import { useCameraStore } from '../stores/camera';
import type { Barn, Pen, CameraConfig, Camera } from '../types';

const barnStore = useBarnStore();
const penStore = usePenStore();
const cameraStore = useCameraStore();

const currentPage = ref(1);
const jumpPage = ref(1);

const barns = ref<Barn[]>([]);
const pens = ref<Pen[]>([]);

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(cameraStore.configTotal / 10);
});

// 跳转到指定页码
const jumpToPage = async () => {
  if (jumpPage.value < 1 || jumpPage.value > totalPages.value) {
    alert('请输入有效的页码');
    return;
  }
  currentPage.value = jumpPage.value;
  await loadCameraConfigs(currentPage.value);
};
const allCameras = ref<Camera[]>([]);
const cameraConfigs = ref<CameraConfig[]>([]);

const newCamera = ref({
  camera_id: '',
  flv_url: '',
  barn_id: '',
  pen_id: '',
  start_time: '09:00',
  end_time: '19:00'
});

const selectedCameraId = ref('');

// 筛选后的摄像头列表
const filteredCameras = computed(() => {
  let result = allCameras.value;
  console.log('Filtering cameras. Barn:', newCamera.value.barn_id, 'Pen:', newCamera.value.pen_id);
  console.log('All cameras:', allCameras.value);

  // 按养殖舍筛选
  if (newCamera.value.barn_id) {
    const barnId = parseInt(newCamera.value.barn_id.toString());
    console.log('Filtering by barn ID:', barnId);
    result = result.filter(camera => camera.barn_id === barnId);
    console.log('After barn filter:', result);
  }

  // 按栏筛选
  if (newCamera.value.pen_id) {
    const penId = parseInt(newCamera.value.pen_id.toString());
    console.log('Filtering by pen ID:', penId);
    result = result.filter(camera => camera.pen_id === penId);
    console.log('After pen filter:', result);
  }

  console.log('Final filtered cameras:', result);
  return result;
});

// 加载养殖舍列表
const loadBarns = async () => {
  try {
    await barnStore.fetchBarns();
    barns.value = barnStore.allBarns;
  } catch (err) {
    console.error('Error loading barns:', err);
  }
};

// 加载栏列表
const loadPens = async () => {
  console.log('Loading pens for barn:', newCamera.value.barn_id);
  console.log('Type of barn_id:', typeof newCamera.value.barn_id);

  if (!newCamera.value.barn_id) {
    console.log('No barn selected');
    pens.value = [];
    newCamera.value.pen_id = '';
    return;
  }

  try {
    const barnId = parseInt(newCamera.value.barn_id.toString());
    console.log('Parsed barn ID:', barnId);
    console.log('Type of parsed barn ID:', typeof barnId);

    // 从penStore中获取所有栏，然后本地筛选
    await penStore.fetchPens();
    const allPens = penStore.allPens;
    console.log('All pens:', allPens);
    const filteredPens = allPens.filter(pen => pen.barn_id === barnId);
    console.log('Filtered pens for barn', barnId, ':', filteredPens);

    pens.value = filteredPens;
    // 不再重置pen_id，保持当前选择
  } catch (err) {
    console.error('Error loading pens:', err);
    pens.value = [];
    // 发生错误时才重置pen_id
    newCamera.value.pen_id = '';
  }
};

// 加载摄像头列表
const loadCameras = async () => {
  try {
    await cameraStore.fetchCameras();
    allCameras.value = cameraStore.allCameras;
    console.log('Cameras loaded:', allCameras.value);
  } catch (err) {
    console.error('Error loading cameras:', err);
    allCameras.value = [];
  }
};

// 加载摄像头配置
const loadCameraConfigs = async (page: number = 1) => {
  try {
    await cameraStore.fetchCameraConfigs(page);
    cameraConfigs.value = cameraStore.allCameraConfigs;
  } catch (err) {
    console.error('Error loading camera configs:', err);
  }
};

const changePage = async (page: number) => {
  if (page < 1) return;
  currentPage.value = page;
  await loadCameraConfigs(page);
};

// 添加摄像头配置
const addCamera = async () => {
  if (!newCamera.value.camera_id || !newCamera.value.flv_url) {
    alert('请选择摄像头');
    return;
  }

  if (!newCamera.value.barn_id || !newCamera.value.pen_id) {
    alert('摄像头信息不完整，请重新选择摄像头');
    return;
  }

  try {
    await cameraStore.createCameraConfig({
      camera_id: newCamera.value.camera_id,
      flv_url: newCamera.value.flv_url,
      barn_id: parseInt(newCamera.value.barn_id.toString()),
      pen_id: parseInt(newCamera.value.pen_id.toString()),
      start_time: newCamera.value.start_time,
      end_time: newCamera.value.end_time
    });
    await loadCameraConfigs();
    // 重置表单
    newCamera.value = {
      camera_id: '',
      flv_url: '',
      barn_id: '',
      pen_id: '',
      start_time: '09:00',
      end_time: '19:00'
    };
    selectedCameraId.value = '';
    pens.value = [];
  } catch (err: any) {
    console.error('Error adding camera config:', err);
    alert('添加摄像头配置失败: ' + (err.response?.data?.detail || err.message));
  }
};

// 切换摄像头状态
const toggleCamera = async (id: number) => {
  try {
    await cameraStore.toggleCameraConfig(id);

    // 加载更新后的配置，检查是否被禁用
    await loadCameraConfigs();

    // 找到该摄像头配置
    const camera = cameraConfigs.value.find(c => c.id === id);
    if (camera && !camera.enable) {
      // 如果被禁用，立即停止检测任务
      try {
        const response = await fetch(`http://localhost:8000/api/camera-configs/${id}/stop`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        const result = await response.json();
        console.log('Stop detection result:', result);
      } catch (stopErr) {
        console.error('Error stopping camera detection:', stopErr);
        // 即使停止失败，也继续执行，因为状态已经更新
      }
    }
  } catch (err: any) {
    console.error('Error toggling camera config:', err);
    alert('切换摄像头状态失败: ' + (err.response?.data?.detail || err.message));
  }
};

// 删除摄像头
const deleteCamera = async (id: number) => {
  if (!confirm('确定要删除这个摄像头配置吗？')) {
    return;
  }

  try {
    // 找到该摄像头配置
    const camera = cameraConfigs.value.find(c => c.id === id);
    if (camera && camera.enable) {
      // 如果启用，先禁用
      await cameraStore.toggleCameraConfig(id);

      // 立即停止检测任务
      try {
        const response = await fetch(`http://localhost:8000/api/camera-configs/${id}/stop`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        const result = await response.json();
        console.log('Stop detection result:', result);
      } catch (stopErr) {
        console.error('Error stopping camera detection:', stopErr);
        // 即使停止失败，也继续执行删除操作
      }
    }

    // 删除摄像头配置
    await cameraStore.deleteCameraConfig(id);
    await loadCameraConfigs();
  } catch (err: any) {
    console.error('Error deleting camera config:', err);
    alert('删除摄像头配置失败: ' + (err.response?.data?.detail || err.message));
  }
};

// 获取养殖舍名称
const getBarnName = (barnId: number): string => {
  if (!Array.isArray(barns.value)) {
    return barnId.toString();
  }
  const barn = barns.value.find(b => b.id === barnId);
  return barn ? barn.name : barnId.toString();
};

// 监听养殖舍变化，加载对应栏列表
const handleBarnChange = async () => {
  console.log('Barn changed:', newCamera.value.barn_id);
  await loadPens();
  selectedCameraId.value = '';
  newCamera.value.camera_id = '';
  newCamera.value.flv_url = '';
  console.log('After loading pens, pens count:', (pens.value || []).length);
};

// 监听栏变化，重置摄像头选择
const handlePenChange = () => {
  selectedCameraId.value = '';
  newCamera.value.camera_id = '';
  newCamera.value.flv_url = '';
};

// 监听摄像头变化，填充摄像头信息
const handleCameraChange = async () => {
  console.log('Camera changed:', selectedCameraId.value);
  console.log('All cameras:', allCameras.value);

  if (selectedCameraId.value) {
    const cameraId = parseInt(selectedCameraId.value.toString());
    console.log('Parsed camera ID:', cameraId);

    const camera = allCameras.value.find(c => c.id === cameraId);
    console.log('Found camera:', camera);

    if (camera) {
      console.log('Filling camera info:', camera);
      newCamera.value.camera_id = camera.camera_id;
      newCamera.value.flv_url = camera.flv_url;
      newCamera.value.barn_id = camera.barn_id.toString();

      // 保存摄像头的pen_id
      const cameraPenId = camera.pen_id.toString();

      // 触发栏列表更新
      console.log('Triggering pen list update for barn:', camera.barn_id);
      await loadPens();

      // 恢复摄像头的pen_id
      newCamera.value.pen_id = cameraPenId;
      console.log('After loading pens, pen_id:', newCamera.value.pen_id);
    }
  }
};

// 组件挂载时加载数据
onMounted(async () => {
  await loadBarns();
  await penStore.fetchPens(); // 提前加载所有栏数据
  await loadCameras();
  await loadCameraConfigs(currentPage.value);
});
</script>

<style scoped>
.camera-config-manager {
  width: 100%;
}

.form {
  margin-bottom: 30px;
  padding: 20px;
  background: #13172f;
  border-radius: 10px;
}

.form-row {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.form-group {
  margin-bottom: 15px;
  flex: 1;
}

.form-group.half {
  flex: 0 0 calc(50% - 7.5px);
}

label {
  font-size: 14px;
  color: #b9c2d0;
  display: block;
  margin: 8px 0 4px;
}

input, select {
  width: 100%;
  padding: 10px;
  border-radius: 10px;
  border: 1px solid #334;
  background: #172045;
  color: #e7e9ee;
  box-sizing: border-box;
}

button {
  cursor: pointer;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid #345;
  background: #1d2a5a;
  color: #e7e9ee;
  transition: background 0.2s;
  margin-top: 10px;
}

button:hover {
  background: #26346e;
}

button:disabled {
  background: #666;
  cursor: not-allowed;
}

.camera-list {
  margin-top: 20px;
}

.table-container {
  overflow-x: auto;
  margin-top: 15px;
}

table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

th, td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #334;
  word-wrap: break-word;
}

th {
  background: #172045;
  color: #60a5fa;
}

th:nth-child(1), td:nth-child(1) {
  width: 60px;
}

th:nth-child(2), td:nth-child(2) {
  width: 100px;
}

th:nth-child(3), td:nth-child(3) {
  width: 300px;
}

th:nth-child(4), td:nth-child(4) {
  width: 100px;
}

th:nth-child(5), td:nth-child(5) {
  width: 80px;
}

th:nth-child(6), td:nth-child(6) {
  width: 150px;
}

th:nth-child(7), td:nth-child(7) {
  width: 80px;
}

th:nth-child(8), td:nth-child(8) {
  width: 120px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form {
    padding: 10px;
  }

  .table-container {
    font-size: 12px;
  }

  th, td {
    padding: 6px 8px;
  }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
  gap: 10px;
}

.pagination button {
  padding: 5px 10px;
  font-size: 14px;
  margin-top: 0;
}

.pagination span {
  padding: 0 10px;
  color: #60a5fa;
  font-weight: bold;
}

.page-jump {
  display: flex;
  align-items: center;
}

.total-records {
  margin-left: 20px;
  color: #b9c2d0;
  font-size: 14px;
}
</style>
