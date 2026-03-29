<template>
  <div class="event-record">
    <h2>事件记录</h2>

    <div class="form-row">
      <div class="form-group">
        <label for="eventBarnId">养殖舍</label>
        <select id="eventBarnId" v-model="selectedBarn" @change="handleBarnChange">
          <option value="">全部养殖舍</option>
          <option
            v-for="barn in barnStore.allBarns"
            :key="barn.id"
            :value="String(barn.id)"
          >
            {{ barn.name }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="eventPenId">养殖栏</label>
        <select id="eventPenId" v-model="selectedPen" @change="handlePenChange">
          <option value="">全部养殖栏</option>
          <option
            v-for="pen in pens"
            :key="pen.id"
            :value="String(pen.id)"
          >
            第{{ pen.pen_number }}栏
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="eventCameraId">摄像头</label>
        <select id="eventCameraId" v-model="selectedCamera" @change="handleCameraChange">
          <option value="">全部摄像头</option>
          <option
            v-for="camera in cameras"
            :key="camera.id"
            :value="String(camera.id)"
          >
            {{ camera.camera_id }}
          </option>
        </select>
      </div>
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
            <th>持续时间(秒)</th>
            <th>平均置信度</th>
            <th>置信图</th>
            <th>所属栏</th>
            <th>所属养殖舍</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="event in eventStore.allEvents" :key="event.id">
            <td>{{ event.id }}</td>
            <td>{{ formatDateTime(event.start_time) }}</td>
            <td>{{ event.duration }}</td>
            <td>{{ event.avg_confidence.toFixed(2) }}</td>
            <td>
              <div class="confidence-image" v-if="event.screenshot">
                <img
                  :src="getImageUrl(event.screenshot)"
                  alt="置信图"
                  class="screenshot-img"
                  @click="openImageModal(getImageUrl(event.screenshot))"
                  style="cursor: pointer;"
                  @error="handleImageError"
                />
              </div>
              <div v-else class="no-image">无截图</div>
            </td>
            <td>{{ event.pen_id }}</td>
            <td>{{ getBarnName(event.barn_id) }}</td>
          </tr>
          <tr v-if="eventStore.allEvents.length === 0">
            <td colspan="7" style="text-align: center;">暂无事件数据</td>
          </tr>
        </tbody>
      </table>

      <div class="pagination">
        <button @click="changePage(1)" :disabled="currentPage === 1">首页</button>
        <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1">上一页</button>
        <span>{{ currentPage }} / {{ totalPages }}</span>
        <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages">下一页</button>
        <div class="page-jump">
          <input
            type="number"
            v-model.number="jumpPage"
            min="1"
            :max="totalPages"
            style="width: 60px; margin: 0 10px;"
          />
          <button @click="jumpToPage">跳转</button>
        </div>
        <span class="total-records">共 {{ eventStore.total }} 条记录</span>
      </div>
    </div>

    <div v-if="showImageModal" class="image-modal" @click="closeImageModal">
      <div class="modal-content" @click.stop>
        <span class="close-btn" @click="closeImageModal">&times;</span>
        <img :src="currentImageUrl" alt="放大图片" class="modal-image" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useBarnStore } from '../stores/barn';
import { useCameraStore } from '../stores/camera';
import { useEventStore } from '../stores/event';
import type { Pen, Camera } from '../types';

const barnStore = useBarnStore();
const cameraStore = useCameraStore();
const eventStore = useEventStore();

const currentPage = ref(1);
const jumpPage = ref(1);

const pens = ref<Pen[]>([]);
const cameras = ref<Camera[]>([]);
const selectedBarn = ref<string>('');
const selectedPen = ref<string>('');
const selectedCamera = ref<string>('');

const showImageModal = ref(false);
const currentImageUrl = ref('');

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(eventStore.total / 10));
});

const dedupeCameras = (list: Camera[]) => {
  return Array.from(new Map(list.map((camera) => [camera.id, camera])).values());
};

const resetToFirstPage = () => {
  currentPage.value = 1;
  jumpPage.value = 1;
};

const loadBarns = async () => {
  try {
    await barnStore.fetchBarns();
  } catch (err) {
    console.error('Error loading barns:', err);
  }
};

const loadPens = async () => {
  if (!selectedBarn.value) {
    pens.value = [];
    selectedPen.value = '';
    return;
  }

  try {
    const penList = await barnStore.fetchBarnPens(Number(selectedBarn.value));
    pens.value = penList;
  } catch (err) {
    console.error('Error loading pens:', err);
    pens.value = [];
  }
};

const loadCameras = async (resetSelection: boolean = true) => {
  if (resetSelection) {
    selectedCamera.value = '';
  }

  try {
    let list: Camera[] = [];

    if (!selectedBarn.value) {
      list = await cameraStore.fetchAllCameras();
    } else if (selectedPen.value) {
      list = await cameraStore.fetchCamerasByPen(Number(selectedPen.value));
    } else {
      list = await cameraStore.fetchCamerasByBarn(Number(selectedBarn.value));
    }

    cameras.value = dedupeCameras(list);
  } catch (err) {
    console.error('Error loading cameras:', err);
    cameras.value = [];
  }
};

const loadEvents = async (page: number = 1) => {
  try {
    if (selectedCamera.value) {
      await eventStore.fetchEventsByCamera(Number(selectedCamera.value), page);
    } else if (selectedPen.value) {
      await eventStore.fetchEventsByPen(Number(selectedPen.value), page);
    } else if (selectedBarn.value) {
      await eventStore.fetchEventsByBarn(Number(selectedBarn.value), page);
    } else {
      await eventStore.fetchEvents(page);
    }
  } catch (err) {
    console.error('Error loading events:', err);
  }
};

const handleBarnChange = async () => {
  selectedPen.value = '';
  resetToFirstPage();
  await loadPens();
  await loadCameras(true);
  await loadEvents(currentPage.value);
};

const handlePenChange = async () => {
  resetToFirstPage();
  await loadCameras(true);
  await loadEvents(currentPage.value);
};

const handleCameraChange = async () => {
  resetToFirstPage();
  await loadEvents(currentPage.value);
};

const changePage = async (page: number) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  jumpPage.value = page;
  await loadEvents(page);
};

const jumpToPage = async () => {
  if (jumpPage.value < 1 || jumpPage.value > totalPages.value) {
    alert('请输入有效的页码');
    return;
  }
  currentPage.value = jumpPage.value;
  await loadEvents(currentPage.value);
};

const formatDateTime = (dateTime: string): string => {
  const date = new Date(dateTime);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
};

const getBarnName = (barnId: number): string => {
  const barn = barnStore.allBarns.find((b) => b.id === barnId);
  return barn ? barn.name : String(barnId);
};

const getImageUrl = (screenshotPath: string): string => {
  if (!screenshotPath) return '';
  if (screenshotPath.startsWith('http://') || screenshotPath.startsWith('https://')) {
    return screenshotPath;
  }
  if (screenshotPath.startsWith('/')) {
    return `http://localhost:8080${screenshotPath}`;
  }
  return `http://localhost:8080/${screenshotPath}`;
};

const openImageModal = (imageUrl: string) => {
  currentImageUrl.value = imageUrl;
  showImageModal.value = true;
};

const closeImageModal = () => {
  showImageModal.value = false;
  currentImageUrl.value = '';
};

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement;
  target.src = '';
  target.alt = '图片加载失败';
};

onMounted(async () => {
  await loadBarns();
  await loadCameras(true);
  await loadEvents(currentPage.value);
});
</script>

<style scoped>
.event-record {
  width: 100%;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
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

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  button {
    width: 100%;
  }

  .table-container {
    font-size: 12px;
  }

  th,
  td {
    padding: 6px 8px;
  }
}

.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  position: relative;
  max-width: 90%;
  max-height: 90%;
}

.close-btn {
  position: absolute;
  top: -40px;
  right: 0;
  color: white;
  font-size: 30px;
  font-weight: bold;
  cursor: pointer;
}

.close-btn:hover {
  color: #ccc;
}

.modal-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 4px;
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
