<template>
  <div class="pen-manager">
    <h2>栏管理</h2>

    <div class="form-row">
      <div class="form-group">
        <label for="penBarnId">所属养殖舍</label>
        <select
          id="penBarnId"
          v-model="penForm.barn_id"
          @change="filterPens"
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
        <label for="penNumber">栏编号</label>
        <input
          type="number"
          id="penNumber"
          v-model="penForm.pen_number"
          placeholder="请输入栏编号"
          min="1"
        >
      </div>
    </div>

    <div class="buttons" style="margin-bottom: 15px;">
      <button
        @click="createPen"
        :disabled="penStore.isLoading || barnStore.isLoading"
      >
        {{ penStore.isLoading ? '添加中...' : '添加栏' }}
      </button>
    </div>

    <div v-if="penStore.error" class="error-message">
      {{ penStore.error }}
    </div>

    <div class="table-container">
      <table id="penTable">
        <thead>
          <tr>
            <th>ID</th>
            <th>栏编号</th>
            <th>所属养殖舍</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pen in filteredPens" :key="pen.id">
            <td>{{ pen.id }}</td>
            <td>{{ pen.pen_number }}</td>
            <td>{{ getBarnName(pen.barn_id) }}</td>
            <td>
              <button @click="deletePen(pen.id)">删除</button>
            </td>
          </tr>
          <tr v-if="filteredPens && filteredPens.length === 0">
            <td colspan="4" style="text-align: center;">暂无栏数据</td>
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
        <span class="total-records">共 {{ penStore.total }} 条记录</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useBarnStore } from '../stores/barn';
import { usePenStore } from '../stores/pen';
import { useCameraStore } from '../stores/camera';
import type { Barn, Pen } from '../types';

const barnStore = useBarnStore();
const penStore = usePenStore();
const cameraStore = useCameraStore();

const currentPage = ref(1);
const jumpPage = ref(1);

const penForm = ref({
  pen_number: 1,
  barn_id: '',
});

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(penStore.total / 10);
});

// 跳转到指定页码
const jumpToPage = async () => {
  if (jumpPage.value < 1 || jumpPage.value > totalPages.value) {
    alert('请输入有效的页码');
    return;
  }
  currentPage.value = jumpPage.value;
  await loadPens(currentPage.value);
};

// 筛选后的栏列表
const filteredPens = ref<Pen[]>([]);

// 加载养殖舍列表
const loadBarns = async () => {
  try {
    await barnStore.fetchBarns();
  } catch (err) {
    console.error('Error loading barns:', err);
  }
};

// 加载栏列表
const loadPens = async (page: number = 1) => {
  try {
    await penStore.fetchPens(page);
    // 加载后筛选
    filterPens();
  } catch (err) {
    console.error('Error loading pens:', err);
  }
};

const changePage = async (page: number) => {
  if (page < 1) return;
  currentPage.value = page;
  await loadPens(page);
};

// 按养殖舍筛选栏列表
const filterPens = () => {
  if (penForm.value.barn_id) {
    // 筛选出属于所选养殖舍的栏
    filteredPens.value = penStore.allPens.filter(pen => pen.barn_id === parseInt(penForm.value.barn_id.toString()));
  } else {
    // 显示所有栏
    filteredPens.value = penStore.allPens;
  }
};

// 获取养殖舍名称
const getBarnName = (barnId: number | undefined): string => {
  if (barnId === undefined || barnId === null) {
    return '未知';
  }
  if (!Array.isArray(barnStore.allBarns)) {
    return barnId.toString();
  }
  const barn = barnStore.allBarns.find(b => b.id === barnId);
  return barn ? barn.name : barnId.toString();
};

// 创建栏
const createPen = async () => {
  if (!penForm.value.barn_id || !penForm.value.pen_number) {
    penStore.error = '请填写完整的栏信息';
    return;
  }

  try {
    await penStore.createPen({
      pen_number: parseInt(penForm.value.pen_number.toString()),
      barn_id: parseInt(penForm.value.barn_id.toString()),
    });

    // 只重置栏编号，保持养殖舍选择
    penForm.value.pen_number = 1;

    // 重新加载栏列表
    await loadPens();
  } catch (err: any) {
    penStore.error = err.response?.data?.detail || '创建栏失败';
  }
};



// 删除栏
const deletePen = async (penId: number) => {
  try {
    // 加载所有摄像头数据
    await cameraStore.fetchCameras();

    // 检查该栏是否有摄像头
    const penCameras = cameraStore.allCameras.filter(camera => camera.pen_id === penId);
    const cameraCount = penCameras.length;

    if (cameraCount > 0) {
      // 弹出确认提示
      const confirmMessage = `这个栏下还有 ${cameraCount} 个摄像头，确定要删除这个栏及其所有摄像头吗？`;

      if (!confirm(confirmMessage)) {
        return;
      }
    } else {
      // 没有摄像头时的普通确认
      if (!confirm('确定要删除这个栏吗？')) {
        return;
      }
    }

    // 执行删除
    await penStore.deletePen(penId);
    // 重新加载栏列表
    await loadPens();
  } catch (err: any) {
    penStore.error = err.response?.data?.detail || '删除栏失败';
  }
};

// 组件挂载时加载数据
onMounted(async () => {
  await loadBarns();
  await loadPens(currentPage.value);
});
</script>

<style scoped>
.pen-manager {
  width: 100%;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 15px;
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
  width: 200px;
}

th:nth-child(4), td:nth-child(4) {
  width: 150px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .buttons {
    flex-direction: column;
  }

  button {
    width: 100%;
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
