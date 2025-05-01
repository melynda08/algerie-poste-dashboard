"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Loader2, RefreshCw } from "lucide-react"
import Image from "next/image"

export default function VisualizePage() {
  const [isLoading, setIsLoading] = useState(false)
  const [visualizationData, setVisualizationData] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)

  const generateVisualization = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem("token")

      if (!token) {
        throw new Error("Authentication token not found")
      }

      const response = await fetch("/api/visualize", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          conversation_id: conversationId,
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to generate visualization")
      }

      const data = await response.json()
      setVisualizationData(data.image)
      setConversationId(data.conversation_id)
    } catch (error) {
      console.error("Visualization error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Data Visualization</h1>
        <p className="text-muted-foreground">Generate visualizations to gain insights about your logistics data</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Shipment Flow Analysis</CardTitle>
          <Button variant="outline" onClick={generateVisualization} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Generate
              </>
            )}
          </Button>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="sunburst" className="space-y-4">
            <TabsList>
              <TabsTrigger value="sunburst">Sunburst</TabsTrigger>
              <TabsTrigger value="sankey">Sankey</TabsTrigger>
              <TabsTrigger value="heatmap">Heatmap</TabsTrigger>
            </TabsList>
            <TabsContent value="sunburst" className="space-y-4">
              <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
                <div className="flex min-h-[400px] items-center justify-center p-4">
                  {isLoading ? (
                    <div className="flex flex-col items-center">
                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                      <p className="mt-2 text-sm text-muted-foreground">Generating visualization...</p>
                    </div>
                  ) : visualizationData ? (
                    <div className="flex justify-center">
                      <Image
                        src={visualizationData || "/placeholder.svg"}
                        alt="Shipment Flow Analysis"
                        width={700}
                        height={500}
                        className="rounded-md"
                      />
                    </div>
                  ) : (
                    <div className="text-center">
                      <p className="text-muted-foreground">
                        Click the Generate button to create a visualization of your shipment flow data.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>
            <TabsContent value="sankey">
              <div className="flex min-h-[400px] items-center justify-center rounded-lg border bg-muted p-4">
                <p className="text-muted-foreground">
                  Sankey diagram visualization will be available in a future update.
                </p>
              </div>
            </TabsContent>
            <TabsContent value="heatmap">
              <div className="flex min-h-[400px] items-center justify-center rounded-lg border bg-muted p-4">
                <p className="text-muted-foreground">Heatmap visualization will be available in a future update.</p>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
