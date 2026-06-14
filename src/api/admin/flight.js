import api from '../index'

export const getAdminFlights = (params = {}) => {
  return api.get('/admin/flights', { params })
}

export const getAdminFlightDetail = (instanceId) => {
  return api.get(`/admin/flights/${instanceId}`)
}

export const getFlightPricing = (instanceId) => {
  return api.get(`/admin/flights/${instanceId}/cabins`)
}

export const createFlightPricing = (instanceId, data) => {
  return api.post(`/admin/flights/${instanceId}/cabins`, data)
}

export const updateFlightPricing = (pricingId, data) => {
  return api.put(`/admin/cabins/${pricingId}`, data)
}

export const getFlightIrregularities = (instanceId) => {
  return api.get(`/admin/flights/${instanceId}/irregularities`)
}

export const createFlightIrregularity = (instanceId, data) => {
  return api.post(`/admin/flights/${instanceId}/irregularities`, data)
}

export const resolveFlightIrregularity = (irregularityId) => {
  return api.put(`/admin/irregularities/${irregularityId}/resolve`)
}

export const getAffectedOrders = (instanceId, params = {}) => {
  return api.get(`/admin/flights/${instanceId}/affected-orders`, { params })
}
