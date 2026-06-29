const SYSTEM_ADMIN_ROLES = [
  '系统总管理员',
  '平台总管理员',
  '总管理员'
]

const PRIMARY_ADMIN_ROLE = '航司主管理员'
const ORDER_ADMIN_ROLE = '订单管理员'
const FLIGHT_ADMIN_ROLE = '航班管理员'

const parseStoredJson = (value) => {
  if (!value) return null

  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

export const getStoredToken = () => {
  return (
    localStorage.getItem('token') ||
    localStorage.getItem('adminToken') ||
    localStorage.getItem('accessToken') ||
    ''
  )
}

const decodeTokenPayload = (token) => {
  if (!token || !token.includes('.')) return null

  try {
    const payload = token.split('.')[1]
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(
      normalized.length + ((4 - normalized.length % 4) % 4),
      '='
    )

    return JSON.parse(decodeURIComponent(escape(window.atob(padded))))
  } catch {
    return null
  }
}

const getUserId = (user) => {
  return Number(user?.user_id || user?.userId || user?.id || 0)
}

export const getAdminRole = (user = getStoredUser()) => {
  return String(
    user?.admin_role ||
    user?.adminRole ||
    user?.administratorRole ||
    ''
  ).trim()
}

export const getUserRole = (user = getStoredUser()) => {
  return String(user?.role || '').trim()
}

const getPrivilegeScore = (user) => {
  const role = getUserRole(user)
  const adminRole = getAdminRole(user)

  if (SYSTEM_ADMIN_ROLES.includes(role) || SYSTEM_ADMIN_ROLES.includes(adminRole)) return 100
  if (adminRole === PRIMARY_ADMIN_ROLE || adminRole === '航空公司主管理员') return 80
  if (adminRole === ORDER_ADMIN_ROLE) return 60
  if (adminRole === FLIGHT_ADMIN_ROLE) return 60
  return 0
}

export const getStoredUser = () => {
  const candidates = []

  for (let i = 0; i < localStorage.length; i += 1) {
    const key = localStorage.key(i)
    const parsed = parseStoredJson(localStorage.getItem(key))

    if (
      parsed &&
      typeof parsed === 'object' &&
      (
        parsed.username ||
        parsed.user_id ||
        parsed.userId ||
        parsed.admin_role ||
        parsed.adminRole
      )
    ) {
      candidates.push(parsed)
    }
  }

  if (!candidates.length) return null

  const tokenPayload = decodeTokenPayload(getStoredToken())
  const tokenUserId = Number(tokenPayload?.user_id || tokenPayload?.userId || 0)

  if (tokenUserId) {
    const matched = candidates.find((item) => getUserId(item) === tokenUserId)

    if (matched) return matched
  }

  return candidates.sort((a, b) => getPrivilegeScore(b) - getPrivilegeScore(a))[0]
}

export const isSystemAdmin = (user = getStoredUser()) => {
  if (!user) return false

  const role = getUserRole(user)
  const adminRole = getAdminRole(user)

  return SYSTEM_ADMIN_ROLES.includes(role) ||
    SYSTEM_ADMIN_ROLES.includes(adminRole)
}

export const isAirlineAdmin = (user = getStoredUser()) => {
  if (!user) return false

  const role = getUserRole(user)

  return [
    '航司管理员',
    '航空公司管理员',
    '航司内部管理员'
  ].includes(role)
}

export const isAirlinePrimaryAdmin = (user = getStoredUser()) => {
  if (!user) return false

  const adminRole = getAdminRole(user)

  return isSystemAdmin(user) ||
    adminRole === PRIMARY_ADMIN_ROLE ||
    adminRole === '航空公司主管理员'
}

export const isOrderAdmin = (user = getStoredUser()) => {
  return getAdminRole(user) === ORDER_ADMIN_ROLE
}

export const isFlightAdmin = (user = getStoredUser()) => {
  return getAdminRole(user) === FLIGHT_ADMIN_ROLE
}

export const canManageFlights = (user = getStoredUser()) => {
  return isAirlinePrimaryAdmin(user) ||
    isFlightAdmin(user)
}

export const canManagePricing = (user = getStoredUser()) => {
  return isAirlinePrimaryAdmin(user) ||
    isFlightAdmin(user)
}

export const canManageChangeRules = (user = getStoredUser()) => {
  return isAirlinePrimaryAdmin(user)
}

export const canManageOrders = (user = getStoredUser()) => {
  return isAirlinePrimaryAdmin(user) ||
    isOrderAdmin(user)
}

export const canManageUsers = (user = getStoredUser()) => {
  return isAirlinePrimaryAdmin(user)
}

export const canManageAdmins = (user = getStoredUser()) => {
  return isAirlinePrimaryAdmin(user)
}

export const canUseCoordination = (user = getStoredUser()) => {
  return isSystemAdmin(user)
}

export const getAirlineScopeParams = (selectedAirlineId) => {
  const user = getStoredUser()

  if (isSystemAdmin(user) && selectedAirlineId) {
    return {
      airline_id: selectedAirlineId
    }
  }

  return {}
}

export const getUserDisplayRole = (user = getStoredUser()) => {
  if (!user) return ''

  if (isSystemAdmin(user)) return '系统总管理员'

  return getAdminRole(user) || getUserRole(user) || ''
}

export const canAssistTicketChanges = (user = getStoredUser()) => {
  return canManageOrders(user)
}


// 订单管理员只读航班相关页面；航司主管理员、航班管理员、系统总管理员可写航班/票价/异常
const __readAdminForFlightPermission = () => {
  const keys = ['adminInfo', 'adminUser', 'currentAdmin', 'userInfo', 'user', 'airAdminUser']

  for (const key of keys) {
    const raw = localStorage.getItem(key) || sessionStorage.getItem(key)
    if (!raw) continue

    try {
      const value = JSON.parse(raw)
      if (value && typeof value === 'object') return value
    } catch (error) {
      // ignore
    }
  }

  return {}
}

const __adminTextForFlightPermission = () => {
  const admin = __readAdminForFlightPermission()

  return [
    admin.role,
    admin.userRole,
    admin.user_role,
    admin.adminRole,
    admin.admin_role,
    admin.roleName,
    admin.role_name,
    admin.position,
    admin.post,
    admin.job,
    admin.title
  ].filter(Boolean).map((item) => String(item).trim())
}

export const canWriteFlightModule = () => {
  const texts = __adminTextForFlightPermission()

  return texts.some((item) =>
    ['系统总管理员', '平台总管理员', '总管理员', '航司主管理员', '航班管理员'].includes(item)
  )
}
