import { createContext, useContext, useState, ReactNode } from 'react'

export interface AuthUser {
  id: number
  email: string
  nom: string
  role: string
}

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  login: (token: string, user: AuthUser) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue>(null!)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('nma_token'))
  const [user, setUser] = useState<AuthUser | null>(() => {
    try {
      const raw = localStorage.getItem('nma_user')
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })

  const login = (t: string, u: AuthUser) => {
    localStorage.setItem('nma_token', t)
    localStorage.setItem('nma_user', JSON.stringify(u))
    setToken(t)
    setUser(u)
  }

  const logout = () => {
    localStorage.removeItem('nma_token')
    localStorage.removeItem('nma_user')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
