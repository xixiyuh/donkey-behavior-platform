import { defineStore } from 'pinia';
import axios from 'axios';
import type { Barn } from '../types';

// 设置axios的基础URL为后端服务器的地址
axios.defaults.baseURL = 'http://localhost:8080';

export const useBarnStore = defineStore('barn', {
  state: () => ({
    barns: [] as Barn[],
    loading: false,
    error: null as string | null,
  }),

  getters: {
    allBarns: (state) => state.barns,
    isLoading: (state) => state.loading,
    hasError: (state) => state.error !== null,
  },

  actions: {
    async fetchBarns() {
      this.loading = true;
      this.error = null;
      try {
        console.log('Fetching barns...');
        const response = await axios.get('/api/barns');
        console.log('Barns response:', response.data);
        this.barns = response.data;
      } catch (error) {
        this.error = '加载养殖舍列表失败';
        console.error('Error fetching barns:', error);
      } finally {
        this.loading = false;
      }
    },

    async createBarn(barn: { name: string; total_pens: number }) {
      this.loading = true;
      this.error = null;
      try {
        console.log('Creating barn:', barn);
        const response = await axios.post('/api/barns', barn);
        console.log('Barn created:', response.data);
        this.barns.push(response.data);
        return response.data;
      } catch (error: any) {
        this.error = error.response?.data?.detail || '创建养殖舍失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async deleteBarn(barnId: number) {
      this.loading = true;
      this.error = null;
      try {
        console.log('Deleting barn:', barnId);
        await axios.delete(`/api/barns/${barnId}`);
        console.log('Barn deleted:', barnId);
        this.barns = this.barns.filter(barn => barn.id !== barnId);
      } catch (error: any) {
        this.error = error.response?.data?.detail || '删除养殖舍失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchBarnPens(barnId: number) {
      this.loading = true;
      this.error = null;
      try {
        console.log('Fetching barn pens:', barnId);
        const response = await axios.get(`/api/barns/${barnId}/pens`);
        console.log('Barn pens response:', response.data);
        return response.data;
      } catch (error) {
        this.error = '加载栏列表失败';
        console.error('Error fetching barn pens:', error);
        return [];
      } finally {
        this.loading = false;
      }
    },

    async fetchBarnEvents(barnId: number) {
      this.loading = true;
      this.error = null;
      try {
        console.log('Fetching barn events:', barnId);
        const response = await axios.get(`/api/barns/${barnId}/mating-events`);
        console.log('Barn events response:', response.data);
        return response.data;
      } catch (error) {
        this.error = '加载事件列表失败';
        console.error('Error fetching barn events:', error);
        return [];
      } finally {
        this.loading = false;
      }
    },
  },
});
