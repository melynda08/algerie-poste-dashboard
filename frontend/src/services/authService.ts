import { API_URL } from "./config"

interface LoginResponse {
  token: string
  user_id: string
  role: string
  expires_in: string
}

export const loginUser = async (email: string, password: string): Promise<LoginResponse> => {
  const response = await fetch(`${API_URL}/login`, {
    method: "POST",
    credentials: "include",  // very important!

    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    throw new Error("Login failed")
  }

  return response.json()
}
