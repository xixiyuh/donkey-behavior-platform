import { defineStore } from 'pinia';
import axios from 'axios';
import type { Camera, CameraConfig } from '../types';

// 设置axios的基础URL为后端服务器的地址
axios.defaults.baseURL = 'http://localhost:8080';

export const useCameraStore = defineStore('camera', {
  state: () => ({
    cameras: [] as Camera[],
    cameraConfigs: [] as CameraConfig[],
    total: 0,
    configTotal: 0,
    loading: false,
    error: null as string | null,
  }),

  getters: {
    allCameras: (state) => state.cameras,
    allCameraConfigs: (state) => state.cameraConfigs,
    isLoading: (state) => state.loading,
    hasError: (state) => state.error !== null,
  },

  actions: {
    async fetchCameras(page: number = 1) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get('/api/cameras', { params: { page } });
        this.cameras = response.data.items;
        this.total = response.data.total;
      } catch (error) {
        this.error = '加载摄像头列表失败';
        console.error('Error fetching cameras:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchAllCameras(pageSize: number = 1000) {
      this.loading = true;
      this.error = null;
      try {
        const allItems: Camera[] = [];
        let page = 1;
        let total = 0;

        while (true) {
          const response = await axios.get('/api/cameras', {
            params: { page, page_size: pageSize },
          });
          const items: Camera[] = response.data.items || [];
          total = response.data.total || 0;
          allItems.push(...items);

          if (items.length < pageSize || allItems.length >= total) {
            break;
          }
          page += 1;
        }

        this.cameras = allItems;
        this.total = total;
        return allItems;
      } catch (error) {
        this.error = 'Failed to fetch all cameras';
        console.error('Error fetching all cameras:', error);
        return [];
      } finally {
        this.loading = false;
      }
    },

    async fetchCamerasByBarn(barnId: number) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get(`/api/cameras/barns/${barnId}/cameras`);
        return response.data as Camera[];
      } catch (error) {
        this.error = 'Failed to fetch cameras by barn';
        console.error('Error fetching cameras by barn:', error);
        return [];
      } finally {
        this.loading = false;
      }
    },

    async fetchCamerasByPen(penId: number) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get(`/api/cameras/pens/${penId}/cameras`);
        return response.data as Camera[];
      } catch (error) {
        this.error = 'Failed to fetch cameras by pen';
        console.error('Error fetching cameras by pen:', error);
        return [];
      } finally {
        this.loading = false;
      }
    },

    async createCamera(camera: {
      camera_id: string;
      pen_id: number;
      barn_id: number;
      flv_url: string;
    }) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post('/api/cameras', camera);
        this.cameras.push(response.data);
        return response.data;
      } catch (error: any) {
        this.error = error.response?.data?.detail || '创建摄像头失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async deleteCamera(cameraId: number) {
      this.loading = true;
      this.error = null;
      try {
        await axios.delete(`/api/cameras/${cameraId}`);
        this.cameras = this.cameras.filter(camera => camera.id !== cameraId);
      } catch (error: any) {
        this.error = error.response?.data?.detail || '删除摄像头失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async updateCamera(cameraId: number, camera: { flv_url: string }) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.put(`/api/cameras/${cameraId}`, camera);
        const index = this.cameras.findIndex(c => c.id === cameraId);
        if (index !== -1) {
          this.cameras[index] = response.data;
        }
        return response.data;
      } catch (error: any) {
        this.error = error.response?.data?.detail || '更新摄像头失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 摄像头配置相关方法
    async fetchCameraConfigs(page: number = 1) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get('/api/camera-configs', { params: { page } });
        this.cameraConfigs = response.data.items;
        this.configTotal = response.data.total;
      } catch (error) {
        this.error = '加载摄像头配置列表失败';
        console.error('Error fetching camera configs:', error);
      } finally {
        this.loading = false;
      }
    },

    async createCameraConfig(config: {
      camera_id: string;
      flv_url: string;
      barn_id: number;
      pen_id: number;
      start_time: string;
      end_time: string;
      status: number;
    }) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post('/api/camera-configs', config);
        this.cameraConfigs.push(response.data);
        return response.data;
      } catch (error: any) {
        this.error = error.response?.data?.detail || '创建摄像头配置失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async setCameraConfigStatus(configId: number, status: number) {
      this.loading = true;
      this.error = null;
      try {
        await axios.patch(`/api/camera-configs/${configId}/status`, { status });
        // 更新本地状态
        const config = this.cameraConfigs.find(c => c.id === configId);
        if (config) {
          config.status = status;
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || '更新摄像头配置状态失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async deleteCameraConfig(configId: number) {
      this.loading = true;
      this.error = null;
      try {
        await axios.delete(`/api/camera-configs/${configId}`);
        this.cameraConfigs = this.cameraConfigs.filter(config => config.id !== configId);
      } catch (error: any) {
        this.error = error.response?.data?.detail || '删除摄像头配置失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },
  },
});
