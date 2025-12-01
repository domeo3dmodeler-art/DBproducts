import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const response = await api.get('/auth/check')
      if (response.data.authenticated) {
        setUser(response.data.user)
      }
    } catch (error) {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login', {
        username,
        password,
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.data.success) {
        setUser(response.data.user)
        return { success: true }
      }
      return { success: false, error: response.data.error || 'Ошибка входа' }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Неверное имя пользователя или пароль',
      }
    }
  }

  const logout = async () => {
    try {
      await api.get('/auth/logout')
      setUser(null)
    } catch (error) {
      console.error('Ошибка выхода:', error)
    }
  }

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    logout,
    checkAuth,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

