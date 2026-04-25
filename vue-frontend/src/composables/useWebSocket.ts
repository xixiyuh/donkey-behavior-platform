import { ref, onUnmounted } from 'vue';
import { WS_BASE_URL } from '../config';

// 后端服务器地址
export function useWebSocket() {
  const ws = ref<WebSocket | null>(null);
  const isConnected = ref(false);
  const error = ref<string | null>(null);
  const frame = ref<string>('');

  const connect = (kind: string, value: string, cameraId?: string, penId?: number, barnId?: number) => {
    // 断开现有连接
    if (ws.value) {
      ws.value.close();
    }

    const qs = new URLSearchParams();
    qs.set('kind', kind);
    if (value) qs.set('value', value);
    if (cameraId) qs.set('camera_id', cameraId);
    if (penId) qs.set('pen_id', penId.toString());
    if (barnId) qs.set('barn_id', barnId.toString());

    // 使用完整的后端WebSocket URL
    const wsUrl = `${WS_BASE_URL}/ws?${qs.toString()}`;

    ws.value = new WebSocket(wsUrl);

    ws.value.onopen = () => {
      isConnected.value = true;
      error.value = null;
    };

    ws.value.onclose = () => {
      isConnected.value = false;
    };

    ws.value.onerror = (e) => {
      error.value = 'WebSocket 连接错误: ' + (e instanceof ErrorEvent ? e.message : '未知错误');
      isConnected.value = false;
    };

    ws.value.onmessage = (ev) => {
      const txt = ev.data;

      // 处理错误消息
      if (typeof txt === 'string' && txt.startsWith('ERROR::')) {
        error.value = txt;
        return;
      }

      // 处理图像帧
      frame.value = txt;
    };
  };

  const disconnect = () => {
    if (ws.value) {
      ws.value.close();
      ws.value = null;
      isConnected.value = false;
      frame.value = '';
    }
  };

  // 组件卸载时断开连接
  onUnmounted(() => {
    disconnect();
  });

  return {
    ws,
    isConnected,
    error,
    frame,
    connect,
    disconnect,
  };
}
