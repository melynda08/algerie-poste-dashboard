"use client"

import { useAuth } from "../contexts/AuthContext"
import { Menu, User, LogOut, Settings } from "lucide-react"
import { useState } from "react"
import { Link } from "react-router-dom"

interface HeaderProps {
  onMenuClick: () => void
}

const Header = ({ onMenuClick }: HeaderProps) => {
  const { user, logout } = useAuth()
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  return (
    <header className="bg-white border-b border-slate-200 py-4 px-4 md:px-6 flex items-center justify-between">
      <div className="flex items-center">
        <button onClick={onMenuClick} className="mr-4 md:hidden text-slate-500 hover:text-slate-700">
          <Menu size={24} />
        </button>
        <h1 className="text-xl font-semibold text-slate-800">RAG Analytics</h1>
      </div>

      <div className="relative">
        <button
          onClick={() => setUserMenuOpen(!userMenuOpen)}
          className="flex items-center space-x-2 text-slate-700 hover:text-slate-900"
        >
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
            <User size={18} />
          </div>
          <span className="hidden md:inline font-medium">{user?.role || "User"}</span>
        </button>

        {userMenuOpen && (
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10 border border-slate-200">
            <Link
              to="/settings"
              className="flex items-center px-4 py-2 text-sm text-slate-700 hover:bg-slate-100"
              onClick={() => setUserMenuOpen(false)}
            >
              <Settings size={16} className="mr-2" />
              Settings
            </Link>
            <button
              onClick={() => {
                logout()
                setUserMenuOpen(false)
              }}
              className="flex items-center w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-slate-100"
            >
              <LogOut size={16} className="mr-2" />
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  )
}

export default Header
