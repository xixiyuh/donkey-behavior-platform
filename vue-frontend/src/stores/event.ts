import { defineStore } from 'pinia';
import axios from 'axios';
import type { MatingEvent } from '../types';

// 设置axios的基础URL为后端服务器的地址
axios.defaults.baseURL = 'http://localhost:8080';

export const useEventStore = defineStore('event', {
  state: () => ({
    events: [] as MatingEvent[],
    total: 0,
    loading: false,
    error: null as string | null,
  }),

  getters: {
    allEvents: (state) => state.events,
    isLoading: (state) => state.loading,
    hasError: (state) => state.error !== null,
  },

  actions: {
    async fetchEvents(page: number = 1) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get('/api/mating-events', { params: { page } });
        this.events = response.data.items;
        this.total = response.data.total;
      } catch (error) {
        this.error = '加载事件列表失败';
        console.error('Error fetching events:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchEventsByPen(penId: number, page: number = 1) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get(`/api/pens/${penId}/mating-events`, { params: { page } });
        this.events = response.data.items;
        this.total = response.data.total;
      } catch (error) {
        this.error = '加载事件列表失败';
        console.error('Error fetching events by pen:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchEventsByBarn(barnId: number, page: number = 1) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get(`/api/barns/${barnId}/mating-events`, { params: { page } });
        this.events = response.data.items;
        this.total = response.data.total;
      } catch (error) {
        this.error = '加载事件列表失败';
        console.error('Error fetching events by barn:', error);
      } finally {
        this.loading = false;
      }
    },
  },
});
