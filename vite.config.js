import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // 解析每一行：
  server: {
    proxy: {
      // 当我们在前端请求以 '/api' 开头的接口时，触发代理拦截
    '/api': {
  target: 'http://127.0.0.1:5000',
  changeOrigin: true
}
    }
  }
})