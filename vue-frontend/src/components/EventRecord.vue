<template>
  <div class="event-record">
    <h2>事件记录</h2>

    <div class="form-row">
      <div class="form-group">
        <label for="eventBarnId">养殖舍</label>
        <select
          id="eventBarnId"
          v-model="selectedBarn"
          @change="loadPens"
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
        <label for="eventPenId">栏</label>
        <select
          id="eventPenId"
          v-model="selectedPen"
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
    </div>

    <div class="buttons" style="margin-bottom: 15px;">
      <button
        @click="loadEvents"
        :disabled="eventStore.isLoading || barnStore.isLoading"
      >
        {{ eventStore.isLoading ? '查询中...' : '查询事件' }}
      </button>
    </div>

    <div v-if="eventStore.error" class="error-message">
      {{ eventStore.error }}
    </div>

    <div class="table-container">
      <table id="eventTable">
        <thead>
          <tr>
            <th>ID</th>
            <th>开始时间</th>
            <th>结束时间</th>
            <th>持续时间(秒)</th>
            <th>平均置信度</th>
            <th>最大置信度</th>
            <th>置信图</th>
            <th>所属摄像头</th>
            <th>所属栏</th>
            <th>所属养殖舍</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="event in eventStore.allEvents" :key="event.id">
            <td>{{ event.id }}</td>
            <td>{{ event.start_time }}</td>
            <td>{{ event.end_time }}</td>
            <td>{{ event.duration }}</td>
            <td>{{ event.avg_confidence.toFixed(2) }}</td>
            <td>{{ event.max_confidence.toFixed(2) }}</td>
            <td>
              <div class="confidence-image" v-if="event.screenshot1">
                <img :src="event.screenshot1" alt="置信图" class="screenshot-img" />
              </div>
              <div v-else class="no-image">无截图</div>
            </td>
            <td>{{ event.camera_id }}</td>
            <td>{{ event.pen_id }}</td>
            <td>{{ getBarnName(event.barn_id) }}</td>
          </tr>
          <tr v-if="eventStore.allEvents.length === 0">
            <td colspan="10" style="text-align: center;">暂无事件数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useBarnStore } from '../stores/barn';
import { useEventStore } from '../stores/event';
import type { Barn, Pen, MatingEvent } from '../types';

const barnStore = useBarnStore();
const eventStore = useEventStore();

const pens = ref<Pen[]>([]);
const selectedBarn = ref<string>('');
const selectedPen = ref<string>('');

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
  if (!selectedBarn.value) {
    pens.value = [];
    selectedPen.value = '';
    return;
  }

  try {
    const penList = await barnStore.fetchBarnPens(parseInt(selectedBarn.value));
    pens.value = penList;
    selectedPen.value = '';
  } catch (err) {
    console.error('Error loading pens:', err);
  }
};

// 加载事件列表
const loadEvents = async () => {
  try {
    if (selectedPen.value) {
      await eventStore.fetchEventsByPen(parseInt(selectedPen.value));
    } else if (selectedBarn.value) {
      await eventStore.fetchEventsByBarn(parseInt(selectedBarn.value));
    } else {
      await eventStore.fetchEvents();
    }
  } catch (err) {
    console.error('Error loading events:', err);
  }
};

// 获取养殖舍名称
const getBarnName = (barnId: number): string => {
  if (!Array.isArray(barnStore.allBarns)) {
    return barnId.toString();
  }
  const barn = barnStore.allBarns.find(b => b.id === barnId);
  return barn ? barn.name : barnId.toString();
};

// 组件挂载时加载数据
onMounted(async () => {
  await loadBarns();
});
</script>

<style scoped>
.event-record {
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
  width: 150px;
}

th:nth-child(3), td:nth-child(3) {
  width: 150px;
}

th:nth-child(4), td:nth-child(4) {
  width: 100px;
}

th:nth-child(5), td:nth-child(5) {
  width: 100px;
}

th:nth-child(6), td:nth-child(6) {
  width: 100px;
}

th:nth-child(7), td:nth-child(7) {
  width: 150px;
}

th:nth-child(8), td:nth-child(8) {
  width: 100px;
}

th:nth-child(9), td:nth-child(9) {
  width: 80px;
}

th:nth-child(10), td:nth-child(10) {
  width: 100px;
}

/* 置信图样式 */
.confidence-image {
  width: 100%;
  height: 100px;
  overflow: hidden;
  border-radius: 4px;
}

.screenshot-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-image {
  width: 100%;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a2332;
  border-radius: 4px;
  color: #888;
  font-size: 12px;
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

  .table-container {
    font-size: 12px;
  }

  th, td {
    padding: 6px 8px;
  }
}
</style>
