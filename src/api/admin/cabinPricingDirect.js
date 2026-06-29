import api from '../index'

export const getPricingFlights = (params = {}) => {
  return api.get('/admin/flights', { params })
}

export const getPricingCabins = (instanceId) => {
  return api.get(`/admin/flights/${instanceId}/cabins`)
}

export const createPricingCabin = (instanceId, data) => {
  return api.post(`/admin/flights/${instanceId}/cabins`, data)
}

export const updatePricingCabin = (pricingId, data) => {
  return api.put(`/admin/cabins/${pricingId}`, data)
}
