// 网络配置

/**
 * 构建API URL
 * @param endpoint API端点
 * @returns 完整的API URL
 */
export function buildApiUrl(endpoint: string): string {
  // 确保endpoint以/开头
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  // 基础URL，与store中的baseURL保持一致
  const baseUrl = 'http://localhost:8080';
  
  return `${baseUrl}${normalizedEndpoint}`;
}
