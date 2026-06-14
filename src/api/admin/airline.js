import api from '../index'

export const getAdminAirlines = (params = {}) => {
  return api.get('/admin/airlines', { params })
}

export const getCrossAirlineCases = (params = {}) => {
  return api.get('/admin/cross-airline/cases', { params })
}
