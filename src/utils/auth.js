const TOKEN_KEY = 'token'
const ROLE_KEY = 'role'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t)
export const removeToken = () => localStorage.removeItem(TOKEN_KEY)

export const getRole = () => localStorage.getItem(ROLE_KEY)
export const setRole = (r) => localStorage.setItem(ROLE_KEY, r)