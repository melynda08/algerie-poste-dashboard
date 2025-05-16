import { API_URL } from "./config"
import { getAuthHeaders } from "./helpers"

interface ChatRequest {
  question: string
  file_id: string
  conversation_id?: string
  embedding_provider?: string
}

export const startConversation = async () => {
  const response = await fetch(`${API_URL}/start_conversation`, {
    method: "POST",
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to start conversation")
  }

  return response.json()
}

export const sendChatMessage = async (data: ChatRequest) => {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error("Failed to send message")
  }

  return response.json()
}

export const getConversationMessages = async (conversationId: string) => {
  const response = await fetch(`${API_URL}/conversation_messages/${conversationId}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch conversation messages")
  }

  return response.json()
}
