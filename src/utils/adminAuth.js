export const getStoredUser = () => {
  try {
    return JSON.parse(localStorage.getItem('currentUser') || '{}')
  } catch (error) {
    console.error('登录用户信息解析失败', error)
    return {}
  }
}

export const isSystemAdmin = (user) => {
  return user?.role === '系统总管理员'
}

export const canManageFlights = (user) => {
  return (
    isSystemAdmin(user) ||
    ['航司主管理员', '航班管理员'].includes(user?.admin_role)
  )
}

export const canManagePricing = (user) => {
  return (
    isSystemAdmin(user) ||
    ['航司主管理员', '订单管理员'].includes(user?.admin_role)
  )
}

export const canManageChangeRules = (user) => {
  return canManagePricing(user)
}

export const canAssistTicketChanges = (user) => {
  return (
    isSystemAdmin(user) ||
    ['航司主管理员', '客服管理员'].includes(user?.admin_role)
  )
}

export const canManageUsers = (user) => {
  return (
    isSystemAdmin(user) ||
    ['航司主管理员', '客服管理员'].includes(user?.admin_role)
  )
}

export const canManageAdmins = (user) => {
  return isSystemAdmin(user) || user?.admin_role === '航司主管理员'
}

export const getAirlineScopeParams = (airlineId) => {
  return airlineId ? { airline_id: airlineId } : {}
}
