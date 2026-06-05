import axios from 'axios'

// 解析每一行：
// axios.create 用来创建一个专门针对我们项目的“快递员”实例
const api = axios.create({
  // baseURL 是所有请求的前缀。写成 '/api' 是为了方便后续解决跨域问题
  baseURL: '/api', 
  // timeout 表示如果后端 5 秒钟还没回消息，就判定为超时报错
  timeout: 5000    
})

// 把配置好的 api 导出去，让其他页面都能用
export default api