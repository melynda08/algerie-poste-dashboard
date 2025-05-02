import { API_URL } from "./config"
import { getAuthHeaders } from "./helpers"

export const getUserHistory = async (userId: string, limit = 20) => {
  const response = await fetch(`${API_URL}/history/${userId}?limit=${limit}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch history")
  }

  return response.json()
}

export const getUserConversations = async (userId: string) => {
  const response = await fetch(`${API_URL}/conversations/${userId}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch conversations")
  }

  return response.json()
}
