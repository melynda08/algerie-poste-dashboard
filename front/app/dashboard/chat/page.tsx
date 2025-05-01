"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { SendHorizontal, Bot, Loader2 } from "lucide-react"
import { Separator } from "@/components/ui/separator"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

type Message = {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

type Conversation = {
  id: string
  startedAt: string
}

export default function ChatPage() {
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Fetch conversations
    fetchConversations()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const fetchConversations = async () => {
    try {
      const token = localStorage.getItem("token")
      const user = JSON.parse(localStorage.getItem("user") || "{}")

      if (!token || !user.id) return

      setIsLoading(true)
      const response = await fetch(`/api/conversations/${user.id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error("Failed to fetch conversations")
      }

      const data = await response.json()
      setConversations(data)

      // If we have conversations and no current one is selected, select the most recent
      if (data.length > 0 && !currentConversationId) {
        setCurrentConversationId(data[0].conversation_id)
      }
    } catch (error) {
      console.error("Error fetching conversations:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const startNewConversation = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) return

      setIsLoading(true)
      const response = await fetch("/api/start-conversation", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        throw new Error("Failed to start new conversation")
      }

      const data = await response.json()
      setCurrentConversationId(data.conversation_id)
      setMessages([])
      fetchConversations()
    } catch (error) {
      console.error("Error starting new conversation:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim() || isLoading) return

    // Create temporary user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: message,
      timestamp: new Date(),
    }

    // Add user message to UI
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    setMessage("")

    try {
      const token = localStorage.getItem("token")
      if (!token) throw new Error("No authentication token found")

      // Start new conversation if needed
      let conversationId = currentConversationId
      if (!conversationId) {
        const startResponse = await fetch("/api/start-conversation", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        })

        if (!startResponse.ok) {
          throw new Error("Failed to start conversation")
        }

        const startData = await startResponse.json()
        conversationId = startData.conversation_id
        setCurrentConversationId(conversationId)
      }

      // Send message to API
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: message,
          conversation_id: conversationId,
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to send message")
      }

      const data = await response.json()

      // Add bot response to UI
      const botMessage: Message = {
        id: Date.now().toString() + 1,
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, botMessage])

      // Refresh conversations list if it's a new conversation
      if (!currentConversationId) {
        fetchConversations()
      }
    } catch (error) {
      console.error("Error sending message:", error)
      // Show error message in chat
      const errorMessage: Message = {
        id: Date.now().toString() + 2,
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleConversationChange = (value: string) => {
    setCurrentConversationId(value)
    setMessages([]) // Clear current messages
    // Here you would normally load the conversation history
    // This would be implemented in a real app
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Chat Assistant</h1>
        <div className="flex items-center gap-4">
          <Select value={currentConversationId || ""} onValueChange={handleConversationChange} disabled={isLoading}>
            <SelectTrigger className="w-60">
              <SelectValue placeholder="Select a conversation" />
            </SelectTrigger>
            <SelectContent>
              {conversations.map((conv) => (
                <SelectItem key={conv.id} value={conv.id}>
                  {new Date(conv.startedAt).toLocaleString()}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={startNewConversation} disabled={isLoading}>
            New Conversation
          </Button>
        </div>
      </div>

      <Card className="flex-1 overflow-hidden">
        <CardContent className="flex h-full flex-col p-0">
          <div className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <Bot className="mb-4 h-16 w-16 text-muted-foreground" />
                <h3 className="text-xl font-medium">Logistics Assistant</h3>
                <p className="mt-2 max-w-md text-muted-foreground">
                  Ask questions about your shipments, packages, logistics data, or anything else related to your mail
                  tracking system.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`flex max-w-[80%] rounded-lg p-4 ${
                        msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                      }`}
                    >
                      <div className="mr-3">
                        <Avatar className="h-8 w-8">
                          {msg.role === "user" ? (
                            <AvatarFallback>U</AvatarFallback>
                          ) : (
                            <>
                              <AvatarImage src="/placeholder.svg?height=32&width=32" alt="AI" />
                              <AvatarFallback>AI</AvatarFallback>
                            </>
                          )}
                        </Avatar>
                      </div>
                      <div>
                        <div className="text-sm">{msg.role === "user" ? "You" : "Assistant"}</div>
                        <div className="mt-1 whitespace-pre-wrap">{msg.content}</div>
                        <div className="mt-1 text-xs opacity-70">{msg.timestamp.toLocaleTimeString()}</div>
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
          <Separator />
          <div className="p-4">
            <form onSubmit={handleSubmit} className="flex space-x-2">
              <Input
                placeholder="Type your message..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                disabled={isLoading}
                className="flex-1"
              />
              <Button type="submit" disabled={isLoading || !message.trim()}>
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <SendHorizontal className="h-4 w-4" />}
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
