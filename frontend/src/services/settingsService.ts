import { API_URL } from "./config"
import { getAuthHeaders } from "./helpers"

interface EmbeddingProviderRequest {
  provider: string
  model: string
}

export const getEmbeddingModels = async () => {
  const response = await fetch(`${API_URL}/embedding_models`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch embedding models")
  }

  return response.json()
}

export const setEmbeddingProvider = async (data: EmbeddingProviderRequest) => {
  const response = await fetch(`${API_URL}/embedding_provider`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error("Failed to set embedding provider")
  }

  return response.json()
}

export const reindexFile = async (fileId: string, provider: string, model?: string) => {
  const response = await fetch(`${API_URL}/reindex`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      file_id: fileId,
      provider,
      model,
    }),
  })

  if (!response.ok) {
    throw new Error("Failed to reindex file")
  }

  return response.json()
}
