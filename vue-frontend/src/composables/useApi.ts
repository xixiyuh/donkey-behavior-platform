import axios from 'axios';
import type { UploadResponse } from '../types';

// 设置axios的基础URL为后端服务器的地址
const API_BASE_URL = 'http://localhost:8080';

export function useApi() {
  const uploadFile = async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading file:', error);
      return {
        success: false,
        message: '文件上传失败',
      };
    }
  };

  const deleteFile = async (filename: string): Promise<{ success: boolean; message: string }> => {
    try {
      const response = await axios.delete(`${API_BASE_URL}/upload/${encodeURIComponent(filename)}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting file:', error);
      return {
        success: false,
        message: '文件删除失败',
      };
    }
  };

  const checkHealth = async (): Promise<{ status: string; detector: string } | null> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      return response.data;
    } catch (error) {
      console.error('Error checking health:', error);
      return null;
    }
  };

  return {
    uploadFile,
    deleteFile,
    checkHealth,
  };
}
