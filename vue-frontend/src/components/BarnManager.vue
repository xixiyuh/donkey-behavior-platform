<template>
  <div class="barn-manager">
    <h2>养殖舍管理</h2>
    <div class="form-row">
      <div class="form-group">
        <label for="barnName">养殖舍名称</label>
        <input type="text" id="barnName" v-model="barnForm.name" placeholder="请输入养殖舍名称" />
      </div>
      <div class="form-group">
        <label for="barnTotalPens">总栏数</label>
        <input type="number" id="barnTotalPens" v-model="barnForm.total_pens" placeholder="请输入总栏数" min="1" max="8" />
      </div>
    </div>
    <div class="buttons">
      <button @click="createBarn" :disabled="barnStore.isLoading">
        {{ barnStore.isLoading ? '添加中...' : '添加养殖舍' }}
      </button>
    </div>
    <div v-if="barnStore.error" class="error-message">
      {{ barnStore.error }}
    </div>
    <div class="table-container">
      <table id="barnTable">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>总栏数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="barn in barnStore.allBarns" :key="barn.id">
            <td>{{ barn.id }}</td>
            <td>{{ barn.name }}</td>
            <td>{{ barn.total_pens }}</td>
            <td>
              <button @click="editBarn(barn)">编辑</button>
              <button @click="deleteBarn(barn.id)">删除</button>
            </td>
          </tr>
          <tr v-if="barnStore.allBarns.length === 0">
            <td colspan="4" style="text-align: center;">暂无养殖舍数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useBarnStore } from '../stores/barn';
import type { Barn } from '../types';

const barnStore = useBarnStore();

const barnForm = ref({
  name: '',
  total_pens: 1,
});

const loadBarns = async () => {
  try {
    await barnStore.fetchBarns();
  } catch (err) {
    console.error('Error loading barns:', err);
  }
};

const createBarn = async () => {
  if (!barnForm.value.name || !barnForm.value.total_pens) {
    barnStore.error = '请填写完整的养殖舍信息';
    return;
  }

  try {
    await barnStore.createBarn({
      name: barnForm.value.name,
      total_pens: parseInt(barnForm.value.total_pens.toString()),
    });

    barnForm.value = {
      name: '',
      total_pens: 1,
    };
  } catch (err: any) {
    barnStore.error = err.response?.data?.detail || '创建养殖舍失败';
  }
};

const editBarn = (barn: Barn) => {
  console.log('Edit barn:', barn);
};

const deleteBarn = async (barnId: number) => {
  if (!confirm('确定要删除这个养殖舍吗？')) {
    return;
  }

  try {
    await barnStore.deleteBarn(barnId);
  } catch (err: any) {
    barnStore.error = err.response?.data?.detail || '删除养殖舍失败';
  }
};

onMounted(async () => {
  await loadBarns();
});
</script>

<style scoped>
.barn-manager {
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
  width: 200px;
}

th:nth-child(3), td:nth-child(3) {
  width: 100px;
}

th:nth-child(4), td:nth-child(4) {
  width: 150px;
}

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
