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
            v-for="barn in barnStore.allBarns || []"
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
            <td>
              <span v-if="!editingCameraId || editingCameraId !== camera.id">{{ camera.flv_url }}</span>
              <input
                v-else
                type="text"
                ref="flvInputRef"
                v-model="editingFlvUrl"
                style="width: 100%; padding: 5px; border-radius: 5px; border: 1px solid #334; background: #172045; color: #e7e9ee;"
              />
            </td>
            <td>
              <template v-if="!editingCameraId || editingCameraId !== camera.id">
                <button @click="startEdit(camera)">操作</button>
                <button @click="deleteCamera(camera.id)">删除</button>
              </template>
              <template v-else>
                <button @click="saveEdit(camera.id)">保存更改</button>
                <button @click="cancelEdit">取消</button>
              </template>
            </td>
          </tr>
          <tr v-if="filteredCameras && filteredCameras.length === 0">
            <td colspan="6" style="text-align: center;">暂无摄像头数据</td>
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
        <span class="total-records">共 {{ cameraStore.total }} 条记录</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { useBarnStore } from '../stores/barn';
import { usePenStore } from '../stores/pen';
import { useCameraStore } from '../stores/camera';
import type { Pen, Camera } from '../types';

const barnStore = useBarnStore();
const penStore = usePenStore();
const cameraStore = useCameraStore();

const currentPage = ref(1);
const jumpPage = ref(1);

const pens = ref<Pen[]>([]);

const cameraForm = ref({
  barn_id: '',
  pen_id: '',
  camera_id: '',
  flv_url: '',
});

// 编辑相关变量
const editingCameraId = ref<number | null>(null);
const editingFlvUrl = ref('');
const flvInputRef = ref<HTMLInputElement | HTMLInputElement[] | null>(null);

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(cameraStore.total / 10);
});

// 跳转到指定页码
const jumpToPage = async () => {
  if (jumpPage.value < 1 || jumpPage.value > totalPages.value) {
    alert('请输入有效的页码');
    return;
  }
  currentPage.value = jumpPage.value;
  await loadCameras(currentPage.value);
};

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
const loadCameras = async (page: number = 1) => {
  try {
    await cameraStore.fetchCameras(page);
    // 加载后筛选
    filterCameras();
  } catch (err) {
    console.error('Error loading cameras:', err);
  }
};

const changePage = async (page: number) => {
  if (page < 1) return;
  currentPage.value = page;
  await loadCameras(page);
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

// 开始编辑FLV地址
const startEdit = (camera: Camera) => {
  editingCameraId.value = camera.id;
  editingFlvUrl.value = camera.flv_url;
  // 延迟聚焦到输入框，确保DOM已经更新
  nextTick(() => {
    focusInput();
  });
};

// 聚焦到输入框并将光标移到最后
const focusInput = () => {
  const input = Array.isArray(flvInputRef.value) ? flvInputRef.value[0] : flvInputRef.value;
  if (!input || typeof input.focus !== 'function') {
    return;
  }

  input.focus();
  const length = input.value.length;
  if (typeof input.setSelectionRange === 'function') {
    input.setSelectionRange(length, length);
  }
};

// 保存编辑
const saveEdit = async (cameraId: number) => {
  if (!editingFlvUrl.value) {
    cameraStore.error = '请输入FLV地址';
    return;
  }

  try {
    await cameraStore.updateCamera(cameraId, {
      flv_url: editingFlvUrl.value,
    });
    cancelEdit();
  } catch (err: any) {
    cameraStore.error = err.response?.data?.detail || '更新摄像头失败';
  }
};

// 取消编辑
const cancelEdit = () => {
  editingCameraId.value = null;
  editingFlvUrl.value = '';
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
  await loadCameras(currentPage.value);
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
