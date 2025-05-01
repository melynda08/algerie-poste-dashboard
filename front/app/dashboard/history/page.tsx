"use client"

import { Button } from "@/components/ui/button"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Loader2, Clock, MessageSquare } from "lucide-react"
import Link from "next/link"

type HistoryItem = {
  question: string
  response: string
  timestamp: string
  conversation_id: string
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem("token")
      const user = JSON.parse(localStorage.getItem("user") || "{}")

      if (!token || !user.id) {
        setIsLoading(false)
        return
      }

      const response = await fetch(`/api/history/${user.id}?limit=30`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error("Failed to fetch history")
      }

      const data = await response.json()
      setHistory(data)
    } catch (error) {
      console.error("Error fetching history:", error)
    } finally {
      setIsLoading(false)
    }
  }

  // Group history by date
  const groupedHistory = history.reduce<{ [key: string]: HistoryItem[] }>((groups, item) => {
    const date = new Date(item.timestamp).toLocaleDateString()
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(item)
    return groups
  }, {})

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-lg">Loading history...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Chat History</h1>
        <p className="text-muted-foreground">View your previous conversations with the logistics assistant</p>
      </div>

      {history.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center p-6">
            <MessageSquare className="mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="text-lg font-medium">No chat history yet</h3>
            <p className="mt-2 text-center text-muted-foreground">
              Start a new conversation with the logistics assistant to see your chat history here.
            </p>
            <Link href="/dashboard/chat" className="mt-4">
              <Button>Start Chatting</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedHistory).map(([date, items]) => (
            <div key={date}>
              <h2 className="mb-4 text-sm font-medium text-muted-foreground">{date}</h2>
              <Card>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {items.map((item, index) => (
                      <div key={index}>
                        <div className="mb-2 flex items-center justify-between">
                          <div className="flex items-center text-sm">
                            <Clock className="mr-1 h-3 w-3 text-muted-foreground" />
                            <span className="text-muted-foreground">
                              {new Date(item.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <Link
                            href={`/dashboard/chat?conversation=${item.conversation_id}`}
                            className="text-xs text-primary hover:underline"
                          >
                            View in Chat
                          </Link>
                        </div>
                        <div className="rounded-lg bg-muted p-3">
                          <p className="font-medium">{item.question}</p>
                        </div>
                        <div className="mt-2 rounded-lg border p-3">
                          <p className="whitespace-pre-wrap text-sm">{item.response}</p>
                        </div>
                        {index !== items.length - 1 && <Separator className="my-4" />}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
