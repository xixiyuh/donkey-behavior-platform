import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiProxyTarget = env.VITE_API_BASE_URL
  const wsProxyTarget = env.VITE_WS_BASE_URL

  return {
    plugins: [
      vue(),
    ],
    server: {
      proxy: {
        ...(apiProxyTarget ? {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path
        },
        '/static': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        },
        '/upload': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        },
        '/health': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        }
        } : {}),
        ...(wsProxyTarget ? {
        '/ws': {
          target: wsProxyTarget,
          ws: true,
          changeOrigin: true,
          secure: false
        }
        } : {})
      }
    }
  }
})
