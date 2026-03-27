import { defineStore } from 'pinia';
import axios from 'axios';
import type { Pen } from '../types';

export const usePenStore = defineStore('pen', {
  state: () => ({
    pens: [] as Pen[],
    loading: false,
    error: null as string | null,
  }),

  getters: {
    allPens: (state) => state.pens,
    isLoading: (state) => state.loading,
    hasError: (state) => state.error !== null,
  },

  actions: {
    async fetchPens() {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get('/api/pens');
        this.pens = response.data;
      } catch (error) {
        this.error = '加载栏列表失败';
        console.error('Error fetching pens:', error);
      } finally {
        this.loading = false;
      }
    },

    async createPen(pen: { pen_number: number; barn_id: number }) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post('/api/pens', pen);
        this.pens.push(response.data);
        return response.data;
      } catch (error: any) {
        this.error = error.response?.data?.detail || '创建栏失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async deletePen(penId: number) {
      this.loading = true;
      this.error = null;
      try {
        await axios.delete(`/api/pens/${penId}`);
        this.pens = this.pens.filter(pen => pen.id !== penId);
      } catch (error: any) {
        this.error = error.response?.data?.detail || '删除栏失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchPenCameras(penId: number) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get(`/api/pens/${penId}/cameras`);
        return response.data;
      } catch (error) {
        this.error = '加载摄像头列表失败';
        console.error('Error fetching pen cameras:', error);
        return [];
      } finally {
        this.loading = false;
      }
    },

    async fetchPenEvents(penId: number) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get(`/api/pens/${penId}/mating-events`);
        return response.data;
      } catch (error) {
        this.error = '加载事件列表失败';
        console.error('Error fetching pen events:', error);
        return [];
      } finally {
        this.loading = false;
      }
    },
  },
});
