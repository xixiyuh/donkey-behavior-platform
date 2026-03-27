import { defineStore } from 'pinia';
import axios from 'axios';
import type { Camera } from '../types';

export const useCameraStore = defineStore('camera', {
  state: () => ({
    cameras: [] as Camera[],
    loading: false,
    error: null as string | null,
  }),

  getters: {
    allCameras: (state) => state.cameras,
    isLoading: (state) => state.loading,
    hasError: (state) => state.error !== null,
  },

  actions: {
    async fetchCameras() {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get('/api/cameras');
        this.cameras = response.data;
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
  },
});
