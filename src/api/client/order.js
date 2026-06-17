import api from '../index.js'

export const createTicketOrder = (data) => {
  return api.post('/orders', {
    passenger_id: data.passengerId,
    pricing_id: data.pricingId,
    seat_no: data.seatNo || ''
  })
}

export const getChangeRecords = () => {
  return api.get('/change-records')
}
