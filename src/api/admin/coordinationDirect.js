import api from '../index'

export const getCoordinationAirlines = () => {
  return api.get('/admin/airlines')
}

export const getCoordinationCases = (params = {}) => {
  return api.get('/admin/cross-airline-cases', { params })
}
