import api from '../index'

export const getAdminOrders = (params = {}) => {
  return api.get('/admin/orders', { params })
}

export const getAdminChangeRecords = (params = {}) => {
  return api.get('/admin/change-records', { params })
}

export const getAdminRefundRecords = (params = {}) => {
  return api.get('/admin/refund-records', { params })
}

export const previewAdminRefund = (orderId, data = {}) => {
  return api.post(`/admin/orders/${orderId}/refund-preview`, data)
}

export const submitAdminRefund = (orderId, data) => {
  return api.post(`/admin/orders/${orderId}/refund`, data)
}

export const previewAdminChange = (orderId, data) => {
  return api.post(`/admin/orders/${orderId}/change-preview`, data)
}

export const submitAdminChange = (orderId, data) => {
  return api.post(`/admin/orders/${orderId}/change`, data)
}
