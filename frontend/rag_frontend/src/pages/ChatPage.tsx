"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { useParams, useNavigate, useLocation } from "react-router-dom"
import { Send, FileText, Settings } from "lucide-react"
import { getUserFiles } from "../services/fileService"
import { sendChatMessage, startConversation, getConversationMessages } from "../services/chatService"
import { useToast } from "../contexts/ToastContext"
import { useAuth } from "../contexts/AuthContext"

interface FileItem {
  file_id: string
  filename: string
}

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

const ChatPage = () => {
  const { fileId } = useParams<{ fileId?: string }>()
  const location = useLocation()
  const [files, setFiles] = useState<FileItem[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(fileId || null)
  const [selectedFileName, setSelectedFileName] = useState<string>("")
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [embeddingProvider, setEmbeddingProvider] = useState<string>("local")
  const [showSettings, setShowSettings] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { showToast } = useToast()
  const navigate = useNavigate()
  const { user } = useAuth()

  // Extract conversation ID from query params if present
  useEffect(() => {
    const queryParams = new URLSearchParams(location.search)
    const convId = queryParams.get("conversationId")
    if (convId) {
      setConversationId(convId)
      loadExistingConversation(convId)
    }
  }, [location])

  useEffect(() => {
    fetchFiles()
  }, [])

  useEffect(() => {
    if (fileId && fileId !== selectedFile) {
      setSelectedFile(fileId)
    }
  }, [fileId])

  useEffect(() => {
    if (selectedFile) {
      const file = files.find((f) => f.file_id === selectedFile)
      if (file) {
        setSelectedFileName(file.filename)
        // Only initialize a new conversation if we don't have one already
        if (!conversationId) {
          initializeConversation()
        }
      }
    }
  }, [selectedFile, files, conversationId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const fetchFiles = async () => {
    try {
      const filesData = await getUserFiles()
      setFiles(filesData)

      if (filesData.length > 0 && !selectedFile) {
        setSelectedFile(filesData[0].file_id)
      }
    } catch (error) {
      showToast("Failed to load files", "error")
    }
  }

  const loadExistingConversation = async (convId: string) => {
    if (!selectedFile) return

    setIsLoading(true)
    try {
      const history = await getConversationMessages(convId)

      // Convert history to messages format
      const loadedMessages: Message[] = []

      history.forEach((item: any) => {
        loadedMessages.push({
          id: `user-${Date.now()}-${Math.random()}`,
          role: "user",
          content: item.question,
          timestamp: new Date(item.timestamp),
        })

        loadedMessages.push({
          id: `assistant-${Date.now()}-${Math.random()}`,
          role: "assistant",
          content: item.response,
          timestamp: new Date(item.timestamp),
        })
      })

      setMessages(loadedMessages)

      // Add welcome back message if no messages
      if (loadedMessages.length === 0) {
        setMessages([
          {
            id: "welcome-back",
            role: "assistant",
            content: `Welcome back to our conversation about "${selectedFileName}". How can I help you?`,
            timestamp: new Date(),
          },
        ])
      }
    } catch (error) {
      showToast("Failed to load conversation history", "error")
      // Fall back to new conversation
      initializeConversation()
    } finally {
      setIsLoading(false)
    }
  }

  const initializeConversation = async () => {
    if (!selectedFile) return

    try {
      const response = await startConversation()
      setConversationId(response.conversation_id)

      // Add welcome message
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: `Hello! I'm ready to help you analyze the data in "${selectedFileName}". What would you like to know?`,
          timestamp: new Date(),
        },
      ])
    } catch (error) {
      showToast("Failed to start conversation", "error")
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newFileId = e.target.value
    setSelectedFile(newFileId)
    // Reset conversation when changing files
    setConversationId(null)
    setMessages([])
    navigate(`/chat/${newFileId}`)
  }

  const handleSendMessage = async () => {
    if (!input.trim() || !selectedFile || !conversationId) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await sendChatMessage({
        question: input,
        file_id: selectedFile,
        conversation_id: conversationId,
        embedding_provider: embeddingProvider,
      })

      const assistantMessage: Message = {
        id: `response-${Date.now()}`,
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])

      // Update embedding provider if it changed
      if (response.embedding_provider) {
        setEmbeddingProvider(response.embedding_provider)
      }
    } catch (error) {
      showToast("Failed to send message", "error")
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const handleEmbeddingProviderChange = (provider: string) => {
    setEmbeddingProvider(provider)
    showToast(`Embedding provider changed to ${provider}`, "info")
    setShowSettings(false)
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <h1 className="text-2xl font-bold text-slate-900 mr-4">Chat</h1>
          <div className="relative">
            <select value={selectedFile || ""} onChange={handleFileChange} className="input py-1 pr-8 pl-3">
              <option value="" disabled>
                Select a file
              </option>
              {files.map((file) => (
                <option key={file.file_id} value={file.file_id}>
                  {file.filename}
                </option>
              ))}
            </select>
            <FileText
              size={16}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-500 pointer-events-none"
            />
          </div>
        </div>

        <div className="relative">
          <button onClick={() => setShowSettings(!showSettings)} className="btn btn-secondary flex items-center">
            <Settings size={16} className="mr-2" />
            Embedding: {embeddingProvider}
          </button>

          {showSettings && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10 border border-slate-200">
              <button
                onClick={() => handleEmbeddingProviderChange("local")}
                className={`flex items-center w-full text-left px-4 py-2 text-sm hover:bg-slate-100 ${
                  embeddingProvider === "local" ? "text-blue-600 font-medium" : "text-slate-700"
                }`}
              >
                Local
              </button>
              <button
                onClick={() => handleEmbeddingProviderChange("openai")}
                className={`flex items-center w-full text-left px-4 py-2 text-sm hover:bg-slate-100 ${
                  embeddingProvider === "openai" ? "text-blue-600 font-medium" : "text-slate-700"
                }`}
              >
                OpenAI
              </button>
              <button
                onClick={() => handleEmbeddingProviderChange("together")}
                className={`flex items-center w-full text-left px-4 py-2 text-sm hover:bg-slate-100 ${
                  embeddingProvider === "together" ? "text-blue-600 font-medium" : "text-slate-700"
                }`}
              >
                Together AI
              </button>
              <button
                onClick={() => handleEmbeddingProviderChange("huggingface")}
                className={`flex items-center w-full text-left px-4 py-2 text-sm hover:bg-slate-100 ${
                  embeddingProvider === "huggingface" ? "text-blue-600 font-medium" : "text-slate-700"
                }`}
              >
                Hugging Face
              </button>
            </div>
          )}
        </div>
      </div>

      {!selectedFile ? (
        <div className="flex-1 flex items-center justify-center bg-white rounded-lg border border-slate-200">
          <div className="text-center p-6">
            <FileText size={48} className="mx-auto text-slate-300" />
            <h3 className="mt-4 text-lg font-medium text-slate-900">No file selected</h3>
            <p className="mt-1 text-sm text-slate-500">Please select a CSV file to start chatting</p>
          </div>
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto bg-white rounded-t-lg border border-slate-200 p-4">
            <div className="space-y-4">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      message.role === "user" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-800"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    <div className={`text-xs mt-1 ${message.role === "user" ? "text-blue-200" : "text-slate-500"}`}>
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-slate-100 rounded-lg px-4 py-3 max-w-[80%]">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 rounded-full bg-slate-300 animate-bounce"></div>
                      <div
                        className="w-2 h-2 rounded-full bg-slate-300 animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                      <div
                        className="w-2 h-2 rounded-full bg-slate-300 animate-bounce"
                        style={{ animationDelay: "0.4s" }}
                      ></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          <div className="bg-white rounded-b-lg border-t-0 border border-slate-200 p-4">
            <div className="flex items-center">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question about your data..."
                className="flex-1 input resize-none"
                rows={2}
                disabled={isLoading || !selectedFile}
              />
              <button
                onClick={handleSendMessage}
                disabled={isLoading || !input.trim() || !selectedFile}
                className={`ml-3 btn ${
                  isLoading || !input.trim() || !selectedFile
                    ? "bg-slate-300 text-slate-500 cursor-not-allowed"
                    : "btn-primary"
                }`}
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ChatPage
