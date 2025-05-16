import { API_URL } from "./config"
import { getAuthHeaders } from "./helpers"

interface VisualizationRequest {
  file_id: string
  prompt?: string
  conversation_id?: string
}

export const generateVisualization = async (data: VisualizationRequest) => {
  const response = await fetch(`${API_URL}/visualize`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error("Failed to generate visualization")
  }

  return response.json()
}
