import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // 解析每一行：
  server: {
    proxy: {
      // 当我们在前端请求以 '/api' 开头的接口时，触发代理拦截
      '/api': {
        // 这里必须填入你们 2 号同学真实的后端电脑 IP 和端口！(假设是 8080)
        target: 'http://localhost:8080', 
        // 允许跨域
        changeOrigin: true,
        // 如果后端的真实接口里没有 '/api' 这几个字，就需要把它替换成空字符串
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})