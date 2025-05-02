import { API_URL } from "./config"
import { getAuthHeaders } from "./helpers"

export const getUserFiles = async () => {
  const response = await fetch(`${API_URL}/csv_files`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch files")
  }

  return response.json()
}

export const uploadFile = async (formData: FormData) => {
  const response = await fetch(`${API_URL}/upload_csv`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(true),
    },
    body: formData,
  })

  if (!response.ok) {
    throw new Error("Failed to upload file")
  }

  return response.json()
}

export const deleteFile = async (fileId: string) => {
  const response = await fetch(`${API_URL}/delete_csv/${fileId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to delete file")
  }

  return response.json()
}

export const getFileMetadata = async (fileId: string) => {
  const response = await fetch(`${API_URL}/csv_metadata/${fileId}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch file metadata")
  }

  return response.json()
}
