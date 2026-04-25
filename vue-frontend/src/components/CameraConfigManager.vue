<template>
  <div class="camera-config-manager">
    <h2>摄像头配置</h2>

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
          <label>栏位</label>
          <select v-model="newCamera.pen_id" @change="handlePenChange">
            <option value="" disabled selected style="color: #888;">请选择栏位</option>
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

      <div class="form-group">
        <label>状态</label>
        <select v-model="newCamera.status">
          <option value="1">启用</option>
          <option value="2">自动</option>
          <option value="0">禁用</option>
        </select>
      </div>

      <button @click="addCamera">新增摄像头配置</button>
    </div>

    <div class="camera-list">
      <h3>已配置摄像头</h3>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>摄像头ID</th>
              <th>FLV地址</th>
              <th>养殖舍</th>
              <th>栏位</th>
              <th>工作时间</th>
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
              <td>{{ getModeText(camera) }}</td>
              <td class="actions-cell">
                <div class="mode-actions">
                  <button
                    class="mode-button"
                    :class="{ active: getModeValue(camera) === 'auto' }"
                    @click="setCameraMode(camera.id, 'auto')"
                  >
                    自动
                  </button>
                  <button
                    class="mode-button"
                    :class="{ active: getModeValue(camera) === 'enabled' }"
                    @click="setCameraMode(camera.id, 'enabled')"
                  >
                    启用
                  </button>
                  <button
                    class="mode-button"
                    :class="{ active: getModeValue(camera) === 'disabled' }"
                    @click="setCameraMode(camera.id, 'disabled')"
                  >
                    禁用
                  </button>
                </div>
                <button class="delete-button" @click="deleteCamera(camera.id)">删除</button>
              </td>
            </tr>
            <tr v-if="cameraConfigs.length === 0">
              <td colspan="8" style="text-align: center;">暂无摄像头配置</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <button @click="changePage(1)" :disabled="currentPage === 1">首页</button>
        <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1">上一页</button>
        <span>{{ currentPage }} / {{ totalPages }}</span>
        <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages">下一页</button>
        <div class="page-jump">
          <input type="number" v-model.number="jumpPage" min="1" :max="totalPages" style="width: 60px; margin: 0 10px;">
          <button @click="jumpToPage">跳转</button>
        </div>
        <span class="total-records">共 {{ cameraStore.configTotal }} 条记录</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useBarnStore } from '../stores/barn';
import { usePenStore } from '../stores/pen';
import { useCameraStore } from '../stores/camera';
import type { Barn, Camera, CameraConfig, Pen } from '../types';

const barnStore = useBarnStore();
const penStore = usePenStore();
const cameraStore = useCameraStore();

const currentPage = ref(1);
const jumpPage = ref(1);

const barns = ref<Barn[]>([]);
const pens = ref<Pen[]>([]);
const allCameras = ref<Camera[]>([]);
const cameraConfigs = ref<CameraConfig[]>([]);
const selectedCameraId = ref('');

const newCamera = ref({
  camera_id: '',
  flv_url: '',
  barn_id: '',
  pen_id: '',
  start_time: '09:00',
  end_time: '19:00',
  status: 1,
});

const totalPages = computed(() => Math.max(1, Math.ceil(cameraStore.configTotal / 10)));

const filteredCameras = computed(() => {
  let result = allCameras.value;

  if (newCamera.value.barn_id) {
    const barnId = Number(newCamera.value.barn_id);
    result = result.filter((camera) => camera.barn_id === barnId);
  }

  if (newCamera.value.pen_id) {
    const penId = Number(newCamera.value.pen_id);
    result = result.filter((camera) => camera.pen_id === penId);
  }

  return result;
});

const loadBarns = async () => {
  await barnStore.fetchBarns();
  barns.value = barnStore.allBarns;
};

const loadPens = async () => {
  if (!newCamera.value.barn_id) {
    pens.value = [];
    newCamera.value.pen_id = '';
    return;
  }

  await penStore.fetchPens();
  const barnId = Number(newCamera.value.barn_id);
  pens.value = penStore.allPens.filter((pen) => pen.barn_id === barnId);
};

const loadCameras = async () => {
  await cameraStore.fetchAllCameras();
  allCameras.value = cameraStore.allCameras;
};

const loadCameraConfigs = async (page = 1) => {
  await cameraStore.fetchCameraConfigs(page);
  cameraConfigs.value = cameraStore.allCameraConfigs;
};

const changePage = async (page: number) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  jumpPage.value = page;
  await loadCameraConfigs(page);
};

const jumpToPage = async () => {
  if (jumpPage.value < 1 || jumpPage.value > totalPages.value) {
    alert('请输入有效页码');
    return;
  }

  currentPage.value = jumpPage.value;
  await loadCameraConfigs(currentPage.value);
};

const getBarnName = (barnId: number): string => {
  const barn = barns.value.find((item) => item.id === barnId);
  return barn ? barn.name : String(barnId);
};

const getModeValue = (camera: CameraConfig): 'auto' | 'enabled' | 'disabled' => {
  if (!camera.enable || camera.status === 0) {
    return 'disabled';
  }

  if (camera.status === 2) {
    return 'auto';
  }

  return 'enabled';
};

const getModeText = (camera: CameraConfig): string => {
  const mode = getModeValue(camera);
  if (mode === 'auto') return '自动';
  if (mode === 'enabled') return '启用';
  return '禁用';
};

const setCameraMode = async (id: number, mode: 'auto' | 'enabled' | 'disabled') => {
  try {
    if (mode === 'disabled') {
      await cameraStore.setCameraConfigEnable(id, 0);
      await cameraStore.setCameraConfigStatus(id, 0);
    } else if (mode === 'enabled') {
      await cameraStore.setCameraConfigEnable(id, 1);
      await cameraStore.setCameraConfigStatus(id, 1);
    } else {
      await cameraStore.setCameraConfigEnable(id, 1);
      await cameraStore.setCameraConfigStatus(id, 2);
    }

    await loadCameraConfigs(currentPage.value);
  } catch (err: any) {
    alert('更新摄像头模式失败: ' + (err.response?.data?.detail || err.message));
  }
};

const addCamera = async () => {
  if (!newCamera.value.camera_id || !newCamera.value.flv_url) {
    alert('请先选择摄像头');
    return;
  }

  if (!newCamera.value.barn_id || !newCamera.value.pen_id) {
    alert('请选择养殖舍和栏位');
    return;
  }

  try {
    await cameraStore.createCameraConfig({
      camera_id: newCamera.value.camera_id,
      flv_url: newCamera.value.flv_url,
      barn_id: Number(newCamera.value.barn_id),
      pen_id: Number(newCamera.value.pen_id),
      start_time: newCamera.value.start_time,
      end_time: newCamera.value.end_time,
      status: Number(newCamera.value.status),
    });

    await loadCameraConfigs(currentPage.value);
    newCamera.value = {
      camera_id: '',
      flv_url: '',
      barn_id: '',
      pen_id: '',
      start_time: '09:00',
      end_time: '19:00',
      status: 1,
    };
    selectedCameraId.value = '';
    pens.value = [];
  } catch (err: any) {
    alert('新增摄像头配置失败: ' + (err.response?.data?.detail || err.message));
  }
};

const deleteCamera = async (id: number) => {
  if (!confirm('确认删除这条摄像头配置吗？')) {
    return;
  }

  try {
    await cameraStore.setCameraConfigEnable(id, 0);
    await cameraStore.setCameraConfigStatus(id, 0);
    await cameraStore.deleteCameraConfig(id);
    await loadCameraConfigs(currentPage.value);
  } catch (err: any) {
    alert('删除摄像头配置失败: ' + (err.response?.data?.detail || err.message));
  }
};

const handleBarnChange = async () => {
  await loadPens();
  selectedCameraId.value = '';
  newCamera.value.camera_id = '';
  newCamera.value.flv_url = '';
};

const handlePenChange = () => {
  selectedCameraId.value = '';
  newCamera.value.camera_id = '';
  newCamera.value.flv_url = '';
};

const handleCameraChange = async () => {
  if (!selectedCameraId.value) return;

  const cameraId = Number(selectedCameraId.value);
  const camera = allCameras.value.find((item) => item.id === cameraId);
  if (!camera) return;

  newCamera.value.camera_id = camera.camera_id;
  newCamera.value.flv_url = camera.flv_url;
  newCamera.value.barn_id = String(camera.barn_id);
  await loadPens();
  newCamera.value.pen_id = String(camera.pen_id);
};

onMounted(async () => {
  await loadBarns();
  await penStore.fetchPens();
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

input,
select {
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
  min-width: 0;
}

.table-container {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  margin-top: 15px;
  -webkit-overflow-scrolling: touch;
}

table {
  width: 100%;
  min-width: 980px;
  border-collapse: collapse;
  table-layout: fixed;
}

th,
td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #334;
  word-wrap: break-word;
}

th {
  background: #172045;
  color: #60a5fa;
}

th:nth-child(1),
td:nth-child(1) {
  width: 60px;
}

th:nth-child(2),
td:nth-child(2) {
  width: 100px;
}

th:nth-child(3),
td:nth-child(3) {
  width: 300px;
}

th:nth-child(4),
td:nth-child(4) {
  width: 100px;
}

th:nth-child(5),
td:nth-child(5) {
  width: 80px;
}

th:nth-child(6),
td:nth-child(6) {
  width: 150px;
}

th:nth-child(7),
td:nth-child(7) {
  width: 90px;
}

th:nth-child(8),
td:nth-child(8) {
  width: 260px;
}

.actions-cell {
  white-space: normal;
}

.mode-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.mode-button,
.delete-button {
  margin-top: 0;
}

.mode-button.active {
  background: #2563eb;
  border-color: #3b82f6;
}

.delete-button {
  margin-top: 8px;
}

@media (max-width: 768px) {
  .form {
    padding: 10px;
  }

  .form-row {
    flex-direction: column;
    gap: 0;
  }

  .form-group.half {
    flex: 1 1 auto;
  }

  .table-container {
    font-size: 12px;
  }

  th,
  td {
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
