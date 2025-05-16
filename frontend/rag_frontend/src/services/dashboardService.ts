import { API_URL } from "./config"
import { getAuthHeaders } from "./helpers"

export interface DashboardVisualization {
  visualization_id: string
  title: string
  image: string
  chart_type: string
  prompt: string
  file_id: string
  file_name: string
  created_at: string
  is_pinned: boolean
  position: number | null
}

export const addVisualizationToDashboard = async (data: {
  title: string
  image: string
  chart_type: string
  prompt: string
  file_id: string
  file_name: string
}) => {
  const response = await fetch(`${API_URL}/add_visualization_to_dashboard`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...data,
      created_at: new Date().toISOString(),
    }),
  })

  if (!response.ok) {
    throw new Error("Failed to add visualization to dashboard")
  }

  return response.json()
}

export const getDashboardVisualizations = async (): Promise<DashboardVisualization[]> => {
  const response = await fetch(`${API_URL}/dashboard_visualizations`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard visualizations")
  }

  return response.json()
}

export const deleteDashboardVisualization = async (visualizationId: string) => {
  const response = await fetch(`${API_URL}/dashboard_visualizations/${visualizationId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to delete visualization")
  }

  return response.json()
}
