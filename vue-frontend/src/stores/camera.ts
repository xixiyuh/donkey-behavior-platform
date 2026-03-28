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

    async toggleCameraConfig(configId: number) {
      this.loading = true;
      this.error = null;
      try {
        await axios.patch(`/api/camera-configs/${configId}/toggle`);
        // 更新本地状态
        const config = this.cameraConfigs.find(c => c.id === configId);
        if (config) {
          config.enable = config.enable === 1 ? 0 : 1;
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || '切换摄像头配置状态失败';
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
