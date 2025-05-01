import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import Link from "next/link"
import { LogIn, Package, BarChart3, MessageSquare } from "lucide-react"

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto text-center mb-12">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl mb-4 text-gray-900 dark:text-white">
            Logistics Tracking System
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Track shipments, analyze logistics data, and get AI-powered insights about your mail and packages.
          </p>
          <div className="mt-8 flex justify-center space-x-4">
            <Button asChild size="lg">
              <Link href="/login">
                <LogIn className="mr-2 h-5 w-5" />
                Sign In
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/register">Create Account</Link>
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Package className="mr-2 h-5 w-5 text-primary" />
                Package Tracking
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-sm">
                Track mail items and receptacles through their entire journey with comprehensive event history.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <MessageSquare className="mr-2 h-5 w-5 text-primary" />
                AI Assistant
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-sm">
                Chat with our AI assistant to get insights about your logistics data and answer your shipping questions.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BarChart3 className="mr-2 h-5 w-5 text-primary" />
                Data Visualization
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-sm">
                Interactive charts and visualizations to analyze shipment flow and identify optimization opportunities.
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
