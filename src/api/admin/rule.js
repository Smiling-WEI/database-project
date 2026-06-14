import api from '../index'

export const getChangeRules = (params = {}) => {
  return api.get('/admin/change-rules', { params })
}

export const createChangeRule = (data) => {
  return api.post('/admin/change-rules', data)
}

export const updateChangeRule = (ruleId, data) => {
  return api.put(`/admin/change-rules/${ruleId}`, data)
}

export const getRefundRules = (params = {}) => {
  return api.get('/admin/refund-rules', { params })
}

export const createRefundRule = (data) => {
  return api.post('/admin/refund-rules', data)
}

export const updateRefundRule = (ruleId, data) => {
  return api.put(`/admin/refund-rules/${ruleId}`, data)
}

export const updateRefundRuleStatus = (ruleId, status) => {
  return api.put(`/admin/refund-rules/${ruleId}/status`, { status })
}
