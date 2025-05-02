"use client"

import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { History, MessageSquare, Search, ChevronDown, ChevronUp } from "lucide-react"
import { getUserHistory, getUserConversations } from "../services/historyService"
import { useAuth } from "../contexts/AuthContext"
import { useToast } from "../contexts/ToastContext"

interface HistoryItem {
  question: string
  response: string
  timestamp: string
  conversation_id: string
  file_id: string
}

interface Conversation {
  conversation_id: string
  started_at: string
  messages: HistoryItem[]
  expanded: boolean
}

const HistoryPage = () => {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const { user } = useAuth()
  const { showToast } = useToast()

  useEffect(() => {
    fetchConversations()
  }, [])

  const fetchConversations = async () => {
    if (!user?.user_id) return

    setIsLoading(true)
    try {
      // First get all conversations
      const conversationsData = await getUserConversations(user.user_id)

      // Then get history items
      const historyData = await getUserHistory(user.user_id, 100)

      // Group history items by conversation
      const conversationsMap: Record<string, HistoryItem[]> = {}

      historyData.forEach((item: HistoryItem) => {
        if (!conversationsMap[item.conversation_id]) {
          conversationsMap[item.conversation_id] = []
        }
        conversationsMap[item.conversation_id].push(item)
      })

      // Create conversation objects with messages
      const conversationsWithMessages = conversationsData.map((conv: any) => ({
        conversation_id: conv.conversation_id,
        started_at: conv.started_at,
        messages: conversationsMap[conv.conversation_id] || [],
        expanded: false,
      }))

      // Sort by most recent first
      conversationsWithMessages.sort((a: { started_at: string | number | Date }, b: { started_at: string | number | Date }) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())

      setConversations(conversationsWithMessages)
    } catch (error) {
      showToast("Failed to load history", "error")
    } finally {
      setIsLoading(false)
    }
  }

  const toggleConversation = (conversationId: string) => {
    setConversations((prevConversations) =>
      prevConversations.map((conv) =>
        conv.conversation_id === conversationId ? { ...conv, expanded: !conv.expanded } : conv,
      ),
    )
  }

  const filteredConversations = searchQuery
    ? conversations.filter((conv) =>
        conv.messages.some(
          (msg) =>
            msg.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
            msg.response.toLowerCase().includes(searchQuery.toLowerCase()),
        ),
      )
    : conversations

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Conversation History</h1>
      </div>

      <div className="card">
        <div className="mb-6">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search conversations..."
              className="input pl-10"
            />
            <Search size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : filteredConversations.length > 0 ? (
          <div className="space-y-6">
            {filteredConversations.map((conversation) => (
              <div key={conversation.conversation_id} className="border border-slate-200 rounded-lg overflow-hidden">
                <div
                  className="bg-slate-50 p-4 flex justify-between items-center cursor-pointer"
                  onClick={() => toggleConversation(conversation.conversation_id)}
                >
                  <div>
                    <h3 className="font-medium text-slate-900">
                      Conversation from {new Date(conversation.started_at).toLocaleString()}
                    </h3>
                    <p className="text-sm text-slate-500">{conversation.messages.length} messages</p>
                  </div>
                  <button className="text-slate-500 hover:text-slate-700">
                    {conversation.expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </button>
                </div>

                {conversation.expanded && (
                  <div className="p-4 space-y-4">
                    {conversation.messages.map((message, idx) => (
                      <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                        <div className="flex justify-between items-start">
                          <h4 className="font-medium text-slate-900">{message.question}</h4>
                          <span className="text-xs text-slate-500 whitespace-nowrap ml-4">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-sm text-slate-600 mt-2">{message.response}</p>
                      </div>
                    ))}

                    <div className="flex justify-end pt-2">
                      <Link
                        to={`/chat/${conversation.messages[0]?.file_id}?conversationId=${conversation.conversation_id}`}
                        className="btn btn-primary flex items-center"
                      >
                        <MessageSquare size={16} className="mr-2" />
                        Continue Conversation
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <History size={48} className="mx-auto text-slate-300" />
            <h3 className="mt-4 text-lg font-medium text-slate-900">No conversation history</h3>
            <p className="mt-1 text-sm text-slate-500">
              {searchQuery ? "No results match your search" : "Start a conversation to see your history"}
            </p>
            {!searchQuery && (
              <div className="mt-6">
                <Link to="/chat" className="btn btn-primary">
                  Start a Conversation
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default HistoryPage
