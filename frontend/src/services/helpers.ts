export const getAuthHeaders = (skipContentType = false) => {
    const token = localStorage.getItem("token")
    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
    }
  
    if (!skipContentType) {
      headers["Content-Type"] = "application/json"
    }
  
    return headers
  }
  