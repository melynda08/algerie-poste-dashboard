"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { BarChart3, Home, MessageCircle, Package, Clock, Settings } from "lucide-react"

type SidebarProps = {
  onNavClick?: () => void
}

export function Sidebar({ onNavClick }: SidebarProps) {
  const pathname = usePathname()

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: Home },
    { name: "Chat Assistant", href: "/dashboard/chat", icon: MessageCircle },
    { name: "Packages", href: "/dashboard/packages", icon: Package },
    { name: "Visualize", href: "/dashboard/visualize", icon: BarChart3 },
    { name: "History", href: "/dashboard/history", icon: Clock },
    { name: "Settings", href: "/dashboard/settings", icon: Settings },
  ]

  return (
    <div className="flex flex-1 flex-col bg-white shadow-sm dark:bg-gray-800">
      <div className="flex h-16 flex-shrink-0 items-center px-4">
        <span className="text-xl font-bold">
          <span className="text-primary">Track</span>Hub
        </span>
      </div>
      <div className="flex flex-1 flex-col overflow-y-auto pt-5 pb-4">
        <nav className="mt-5 flex-1 space-y-1 px-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onNavClick}
                className={cn(
                  "group flex items-center rounded-md px-2 py-2 text-sm font-medium",
                  isActive
                    ? "bg-gray-100 text-primary dark:bg-gray-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white",
                )}
              >
                <item.icon
                  className={cn(
                    "mr-3 h-5 w-5 flex-shrink-0",
                    isActive
                      ? "text-primary"
                      : "text-gray-400 group-hover:text-gray-500 dark:text-gray-400 dark:group-hover:text-gray-300",
                  )}
                  aria-hidden="true"
                />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
