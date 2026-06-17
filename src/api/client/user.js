import api from '../index.js'

export const getMyPassengers = () => api.get('/passengers')

export const addPassenger = (data) => {
  // 前端驼峰 (realName) 转 后端下划线 (real_name)
  return api.post('/passengers', {
    real_name: data.realName,
    id_card: data.idCard,
    phone: data.phone
  })
}