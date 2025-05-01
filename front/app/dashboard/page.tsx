"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Package, Truck, AlertCircle, CheckCircle2, Clock, Loader2 } from "lucide-react"

// Mock data - would be replaced with real API calls in production
const dashboardStats = {
  totalPackages: 358,
  inTransit: 124,
  delivered: 198,
  delayed: 36,
}

const recentActivity = [
  {
    id: 1,
    item: "PKG123456789",
    event: "Arrived at destination facility",
    timestamp: "2023-07-15T09:45:00",
    status: "in-transit",
  },
  {
    id: 2,
    item: "RCP987654321",
    event: "Departed origin facility",
    timestamp: "2023-07-15T08:30:00",
    status: "in-transit",
  },
  {
    id: 3,
    item: "PKG223344556",
    event: "Out for delivery",
    timestamp: "2023-07-15T07:15:00",
    status: "out-for-delivery",
  },
  { id: 4, item: "PKG887766554", event: "Delivered", timestamp: "2023-07-14T16:20:00", status: "delivered" },
  { id: 5, item: "RCP112233445", event: "Processed at origin", timestamp: "2023-07-14T14:10:00", status: "processed" },
]

export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState(true)

  // Simulate loading data
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 1000)
    return () => clearTimeout(timer)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case "delivered":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
      case "in-transit":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300"
      case "out-for-delivery":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300"
      case "delayed":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-lg">Loading dashboard...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your logistics operation</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Packages</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.totalPackages}</div>
            <p className="text-xs text-muted-foreground">All tracked packages in the system</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Transit</CardTitle>
            <Truck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.inTransit}</div>
            <p className="text-xs text-muted-foreground">Packages currently in transit</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Delivered</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.delivered}</div>
            <p className="text-xs text-muted-foreground">Successfully delivered packages</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Delayed</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.delayed}</div>
            <p className="text-xs text-muted-foreground">Packages with delivery issues</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="recent" className="space-y-4">
        <TabsList>
          <TabsTrigger value="recent">Recent Activity</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>
        <TabsContent value="recent" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Package Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-center">
                    <div className="mr-2 flex h-9 w-9 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
                      <Package className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                    </div>
                    <div className="ml-2 space-y-1">
                      <p className="text-sm font-medium">{activity.item}</p>
                      <div className="flex items-center">
                        <p className="text-xs text-gray-500 dark:text-gray-400">{activity.event}</p>
                        <Badge className={`ml-2 ${getStatusColor(activity.status)}`}>
                          {activity.status.replace(/-/g, " ")}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-400 dark:text-gray-500">
                        <Clock className="mr-1 inline-block h-3 w-3" />
                        {new Date(activity.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>Active Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-md bg-yellow-50 p-4 dark:bg-yellow-900/20">
                <div className="flex">
                  <div className="shrink-0">
                    <AlertCircle className="h-5 w-5 text-yellow-400" aria-hidden="true" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-300">Weather Delay Alert</h3>
                    <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-200">
                      <p>
                        Severe weather conditions are affecting deliveries in the Midwest region. Expect delays of 1-2
                        days for affected shipments.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
