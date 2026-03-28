<template>
  <div class="camera-manager">
    <h2>摄像头管理</h2>

    <div class="form-group">
      <label for="cameraBarnId">所属养殖舍</label>
      <select
          id="cameraBarnId"
          v-model="cameraForm.barn_id"
          @change="() => { loadPens(); filterCameras(); }"
        >
          <option value="" disabled selected style="color: #888;">请选择养殖舍</option>
          <option
            v-for="barn in barnStore.allBarns"
            :key="barn.id"
            :value="barn.id"
          >
            {{ barn.name }}
          </option>
        </select>
    </div>

    <div class="form-group">
      <label for="cameraPenId">所属栏</label>
      <select
          id="cameraPenId"
          v-model="cameraForm.pen_id"
          @change="filterCameras"
        >
          <option value="" disabled selected style="color: #888;">请选择栏号</option>
          <option
            v-for="pen in pens"
            :key="pen.id"
            :value="pen.id"
          >
            第{{ pen.pen_number }}栏
          </option>
        </select>
    </div>

    <div class="form-group">
      <label for="cameraId">摄像头标识</label>
      <input
        type="text"
        id="cameraId"
        v-model="cameraForm.camera_id"
        placeholder="请输入摄像头标识（如1-1）"
      >
    </div>

    <div class="form-group">
      <label for="cameraFlvUrl">FLV直播地址</label>
      <input
        type="text"
        id="cameraFlvUrl"
        v-model="cameraForm.flv_url"
        placeholder="请输入FLV直播地址"
      >
    </div>

    <div class="buttons" style="margin-bottom: 15px;">
      <button
        @click="createCamera"
        :disabled="cameraStore.isLoading || barnStore.isLoading"
      >
        {{ cameraStore.isLoading ? '添加中...' : '添加摄像头' }}
      </button>
    </div>

    <div v-if="cameraStore.error" class="error-message">
      {{ cameraStore.error }}
    </div>

    <div class="table-container">
      <table id="cameraTable">
        <thead>
          <tr>
            <th>ID</th>
            <th>摄像头标识</th>
            <th>所属栏</th>
            <th>所属养殖舍</th>
            <th>FLV地址</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="camera in filteredCameras" :key="camera.id">
            <td>{{ camera.id }}</td>
            <td>{{ camera.camera_id }}</td>
            <td>{{ camera.pen_id }}</td>
            <td>{{ getBarnName(camera.barn_id) }}</td>
            <td>{{ camera.flv_url }}</td>
            <td>
              <button @click="editCamera(camera)">编辑</button>
              <button @click="deleteCamera(camera.id)">删除</button>
            </td>
          </tr>
          <tr v-if="filteredCameras.length === 0">
            <td colspan="6" style="text-align: center;">暂无摄像头数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useBarnStore } from '../stores/barn';
import { usePenStore } from '../stores/pen';
import { useCameraStore } from '../stores/camera';
import type { Barn, Pen, Camera } from '../types';

const barnStore = useBarnStore();
const penStore = usePenStore();
const cameraStore = useCameraStore();

const pens = ref<Pen[]>([]);

const cameraForm = ref({
  barn_id: '',
  pen_id: '',
  camera_id: '',
  flv_url: '',
});

// 筛选后的摄像头列表
const filteredCameras = ref<Camera[]>([]);

// 加载养殖舍列表
const loadBarns = async () => {
  try {
    await barnStore.fetchBarns();
  } catch (err) {
    console.error('Error loading barns:', err);
  }
};

// 加载栏列表
const loadPens = async () => {
  if (!cameraForm.value.barn_id) {
    pens.value = [];
    cameraForm.value.pen_id = '';
    return;
  }

  try {
    const penList = await barnStore.fetchBarnPens(parseInt(cameraForm.value.barn_id.toString()));
    pens.value = penList;
    cameraForm.value.pen_id = '';
  } catch (err) {
    console.error('Error loading pens:', err);
  }
};

// 加载摄像头列表
const loadCameras = async () => {
  try {
    await cameraStore.fetchCameras();
    // 加载后筛选
    filterCameras();
  } catch (err) {
    console.error('Error loading cameras:', err);
  }
};

// 按养殖舍和栏筛选摄像头列表
const filterCameras = () => {
  let result = cameraStore.allCameras;

  // 按养殖舍筛选
  if (cameraForm.value.barn_id) {
    const barnId = parseInt(cameraForm.value.barn_id.toString());
    result = result.filter(camera => camera.barn_id === barnId);
  }

  // 按栏筛选
  if (cameraForm.value.pen_id) {
    const penId = parseInt(cameraForm.value.pen_id.toString());
    result = result.filter(camera => camera.pen_id === penId);
  }

  filteredCameras.value = result;
};

// 获取养殖舍名称
const getBarnName = (barnId: number): string => {
  if (!Array.isArray(barnStore.allBarns)) {
    return barnId.toString();
  }
  const barn = barnStore.allBarns.find(b => b.id === barnId);
  return barn ? barn.name : barnId.toString();
};

// 创建摄像头
const createCamera = async () => {
  if (!cameraForm.value.barn_id || !cameraForm.value.pen_id || !cameraForm.value.camera_id || !cameraForm.value.flv_url) {
    cameraStore.error = '请填写完整的摄像头信息';
    return;
  }

  try {
    await cameraStore.createCamera({
      camera_id: cameraForm.value.camera_id,
      pen_id: parseInt(cameraForm.value.pen_id.toString()),
      barn_id: parseInt(cameraForm.value.barn_id.toString()),
      flv_url: cameraForm.value.flv_url,
    });

    // 只重置摄像头标识和FLV地址，保持养殖舍和栏选择
    cameraForm.value.camera_id = '';
    cameraForm.value.flv_url = '';

    // 重新加载摄像头列表
    await loadCameras();
  } catch (err: any) {
    cameraStore.error = err.response?.data?.detail || '创建摄像头失败';
  }
};

// 编辑摄像头
const editCamera = (camera: Camera) => {
  // 这里可以实现编辑功能，弹出模态框或跳转到编辑页面
  console.log('Edit camera:', camera);
};

// 删除摄像头
const deleteCamera = async (cameraId: number) => {
  if (!confirm('确定要删除这个摄像头吗？')) {
    return;
  }

  try {
    await cameraStore.deleteCamera(cameraId);
    // 重新加载摄像头列表
    await loadCameras();
  } catch (err: any) {
    cameraStore.error = err.response?.data?.detail || '删除摄像头失败';
  }
};

// 组件挂载时加载数据
onMounted(async () => {
  await loadBarns();
  await loadCameras();
});
</script>

<style scoped>
.camera-manager {
  width: 100%;
}

.form-group {
  margin-bottom: 15px;
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

.buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 15px;
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

.error-message {
  background: #7f1d1d;
  color: #fecaca;
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 15px;
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
  width: 80px;
}

th:nth-child(4), td:nth-child(4) {
  width: 100px;
}

th:nth-child(5), td:nth-child(5) {
  width: 300px;
}

th:nth-child(6), td:nth-child(6) {
  width: 120px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .buttons {
    flex-direction: column;
  }

  button {
    width: 100%;
  }

  .table-container {
    font-size: 12px;
  }

  th, td {
    padding: 6px 8px;
  }
}
</style>
