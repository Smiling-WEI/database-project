import api from '../index'

export const getAdminUsers = (params = {}) => {
  return api.get('/admin/users', { params })
}
