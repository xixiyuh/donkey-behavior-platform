const SUPPORTED_STREAM_URL_PREFIXES = [
  'http://',
  'https://',
  'rtsp://',
  'rtmp://',
  'flv://',
  'hls://',
];

export const STREAM_URL_ERROR_MESSAGE =
  '直播地址输入不合法，请以 http://、https://、rtsp://、rtmp://、flv:// 或 hls:// 开头';

export const normalizeStreamUrl = (value: string): string => value.trim();

export const isValidStreamUrl = (value: string): boolean => {
  const normalized = normalizeStreamUrl(value).toLowerCase();
  return SUPPORTED_STREAM_URL_PREFIXES.some((prefix) => normalized.startsWith(prefix));
};
