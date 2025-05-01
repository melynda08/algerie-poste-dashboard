"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Menu, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Sidebar } from "@/components/sidebar"
import { TopNav } from "@/components/top-nav"
import '../globals.css'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [isClient, setIsClient] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const router = useRouter()

  useEffect(() => {
    setIsClient(true)
    // Check if token exists, if not redirect to login
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
    }
  }, [router])

  if (!isClient) {
    return null // Return null on server-side rendering
  }

  const handleLogout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    router.push("/login")
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-100 dark:bg-gray-900">
      {/* Mobile sidebar toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed left-4 top-4 z-50 md:hidden"
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
      >
        {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Sidebar for desktop */}
      <div className="hidden md:flex md:w-64 md:flex-col">
        <Sidebar />
      </div>

      {/* Mobile sidebar */}
      <div
        className={cn(
          "fixed inset-0 z-40 flex w-full transform flex-col bg-white p-4 transition-transform duration-200 ease-in-out dark:bg-gray-800 md:hidden",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <Sidebar onNavClick={() => setIsSidebarOpen(false)} />
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNav onLogout={handleLogout} />
        <main className="flex-1 overflow-y-auto p-4">{children}</main>
      </div>
    </div>
  )
}
