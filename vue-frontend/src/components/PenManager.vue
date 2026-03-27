<template>
  <div class="pen-manager">
    <h2>栏管理</h2>

    <div class="form-row">
      <div class="form-group">
        <label for="penBarnId">所属养殖舍</label>
        <select
          id="penBarnId"
          v-model="penForm.barn_id"
        >
          <option value="">请选择养殖舍</option>
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
          <tr v-for="pen in penStore.allPens" :key="pen.id">
            <td>{{ pen.id }}</td>
            <td>{{ pen.pen_number }}</td>
            <td>{{ getBarnName(pen.barn_id) }}</td>
            <td>
              <button @click="editPen(pen)">编辑</button>
              <button @click="deletePen(pen.id)">删除</button>
            </td>
          </tr>
          <tr v-if="penStore.allPens.length === 0">
            <td colspan="4" style="text-align: center;">暂无栏数据</td>
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
import type { Barn, Pen } from '../types';

const barnStore = useBarnStore();
const penStore = usePenStore();

const penForm = ref({
  barn_id: 0,
  pen_number: 1,
});

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
  try {
    await penStore.fetchPens();
  } catch (err) {
    console.error('Error loading pens:', err);
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

    // 重置表单
    penForm.value = {
      barn_id: 0,
      pen_number: 1,
    };
  } catch (err: any) {
    penStore.error = err.response?.data?.detail || '创建栏失败';
  }
};

// 编辑栏
const editPen = (pen: Pen) => {
  // 这里可以实现编辑功能，弹出模态框或跳转到编辑页面
  console.log('Edit pen:', pen);
};

// 删除栏
const deletePen = async (penId: number) => {
  if (!confirm('确定要删除这个栏吗？')) {
    return;
  }

  try {
    await penStore.deletePen(penId);
  } catch (err: any) {
    penStore.error = err.response?.data?.detail || '删除栏失败';
  }
};

// 组件挂载时加载数据
onMounted(async () => {
  await loadBarns();
  await loadPens();
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
</style>
