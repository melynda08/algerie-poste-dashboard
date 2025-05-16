"use client"

import type React from "react"
import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { loginUser } from "../services/authService"
import { useToast } from "./ToastContext"

interface AuthContextType {
  isAuthenticated: boolean
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
}

interface User {
  user_id: string
  role: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const { showToast } = useToast()

  useEffect(() => {
    // Check if user is already logged in
    const storedToken = localStorage.getItem("token")
    const storedUser = localStorage.getItem("user")

    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
      setIsAuthenticated(true)
    }
  }, [])

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await loginUser(email, password)

      if (response.token) {
        const userData = {
          user_id: response.user_id,
          role: response.role,
        }

        setToken(response.token)
        setUser(userData)
        setIsAuthenticated(true)

        localStorage.setItem("token", response.token)
        localStorage.setItem("user", JSON.stringify(userData))

        return true
      }
      return false
    } catch (error) {
      showToast("Login failed. Please check your credentials.", "error")
      return false
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    setIsAuthenticated(false)
    localStorage.removeItem("token")
    localStorage.removeItem("user")
  }

  const value = {
    isAuthenticated,
    user,
    token,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
