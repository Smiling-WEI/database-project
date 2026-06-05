import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'  // <-- 新增：引入路由器

const app = createApp(App)
app.use(ElementPlus)
app.use(router)                // <-- 新增：使用路由器
app.mount('#app')