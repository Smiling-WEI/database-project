import api from '../index.js'

const toApiPayload = (data) => ({
  real_name: data.realName,
  id_card: data.idCard,
  phone: data.phone,
  relation_note: data.relationNote || data.relation || ''
})

export const getPassengers = () => {
  return api.get('/passengers')
}

export const addPassenger = (data) => {
  return api.post('/passengers', toApiPayload(data))
}

export const updatePassenger = (passengerId, data) => {
  return api.put(`/passengers/${passengerId}`, toApiPayload(data))
}

export const deletePassenger = (passengerId) => {
  return api.delete(`/passengers/${passengerId}`)
}
