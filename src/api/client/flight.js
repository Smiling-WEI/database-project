import api from '../index.js'

export const searchFlights = (params) => {
  return api.get('/flights/search', { params })
}

export const getFlightCabins = (instanceId) => {
  return api.get(`/flights/${instanceId}/cabins`)
}
