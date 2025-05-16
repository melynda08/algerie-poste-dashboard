"use client"

import type React from "react"
import { createContext, useContext, useState, type ReactNode } from "react"

type ToastType = "success" | "error" | "info" | "warning"

interface Toast {
  id: string // previously: number
  message: string
  type: ToastType
}

interface ToastContextType {
  toasts: Toast[]
  showToast: (message: string, type: ToastType) => void
  hideToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export const useToast = () => {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider")
  }
  return context
}

interface ToastProviderProps {
  children: ReactNode
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([])
  const [nextId, setNextId] = useState(1)

  const showToast = (message: string, type: ToastType = "info") => {
    const id = crypto.randomUUID()
  
    const toast = { id, message, type }
    setToasts((prevToasts) => [...prevToasts, toast])
  
    setTimeout(() => {
      return hideToast(id)
    }, 5000)
  }
  

  const hideToast = (id: string) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id))
  }
  

  return (
    <ToastContext.Provider value={{ toasts, showToast, hideToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`px-4 py-3 rounded-md shadow-md flex items-center justify-between ${
              toast.type === "success"
                ? "bg-green-500 text-white"
                : toast.type === "error"
                  ? "bg-red-500 text-white"
                  : toast.type === "warning"
                    ? "bg-yellow-500 text-white"
                    : "bg-blue-500 text-white"
            }`}
          >
            <span>{toast.message}</span>
            <button onClick={() => hideToast(toast.id)} className="ml-4 text-white hover:text-gray-200">
              &times;
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
