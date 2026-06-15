import { createContext, useContext, useEffect, useState } from 'react'
import { apiFetch, clearToken, loginRequest, setToken } from '../api/client'

const AuthContext = createContext(null)

function applyTheme(theme) {
  const safeTheme = theme === 'dark' ? 'dark' : 'light'
  document.documentElement.dataset.theme = safeTheme
  localStorage.setItem('theme_preference', safeTheme)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  async function loadMe() {
    try {
      const me = await apiFetch('/auth/me')
      setUser(me)
      applyTheme(me.theme_preference)
      return me
    } catch (_) {
      clearToken()
      setUser(null)
      applyTheme(localStorage.getItem('theme_preference') || 'light')
      return null
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    applyTheme(localStorage.getItem('theme_preference') || 'light')
    loadMe()
  }, [])

  async function login(email, password) {
    const data = await loginRequest(email, password)
    setToken(data.access_token)
    setUser(data.user)
    applyTheme(data.user.theme_preference)
  }

  function logout() {
    clearToken()
    setUser(null)
  }

  function setTheme(theme) {
    applyTheme(theme)
    setUser(prev => prev ? { ...prev, theme_preference: theme === 'dark' ? 'dark' : 'light' } : prev)
  }

  return <AuthContext.Provider value={{ user, loading, login, logout, reload: loadMe, setTheme }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
