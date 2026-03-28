// 养殖舍类型
export interface Barn {
  id: number;
  name: string;
  total_pens: number;
  created_at?: string;
}

// 栏类型
export interface Pen {
  id: number;
  pen_number: number;
  barn_id: number;
  created_at?: string;
}

// 摄像头类型
export interface Camera {
  id: number;
  camera_id: string;
  pen_id: number;
  barn_id: number;
  flv_url: string;
  created_at?: string;
}

// 交配事件类型
export interface MatingEvent {
  id: number;
  start_time: string;
  end_time: string;
  duration: number;
  avg_confidence: number;
  max_confidence: number;
  camera_id: string;
  pen_id: number;
  barn_id: number;
  screenshot?: string;
  created_at?: string;
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'frame' | 'error';
  data: string;
}

// 上传文件响应类型
export interface UploadResponse {
  success: boolean;
  file_path?: string;
  message?: string;
}

// 摄像头配置类型
export interface CameraConfig {
  id: number;
  camera_id: string;
  flv_url: string;
  barn_id: number;
  pen_id: number;
  start_time: string;
  end_time: string;
  enable: number;
  created_at?: string;
}
