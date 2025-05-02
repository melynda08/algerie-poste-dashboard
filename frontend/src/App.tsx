"use client"

import { Routes, Route, Navigate } from "react-router-dom"
import { useAuth } from "./contexts/AuthContext"
import LoginPage from "./pages/LoginPage"
import DashboardPage from "./pages/DashboardPage"
import FilesPage from "./pages/FilesPage"
import ChatPage from "./pages/ChatPage"
import SettingsPage from "./pages/SettingsPage"
import Layout from "./components/Layout"
import ProtectedRoute from "./components/ProtectedRoute"
import VisualizationPage from "./pages/VisualizationPage"
import HistoryPage from "./pages/HistoryPage"

function App() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/dashboard" />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/files" element={<FilesPage />} />
        <Route path="/chat/:fileId?" element={<ChatPage />} />
        <Route path="/visualize/:fileId?" element={<VisualizationPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} />
    </Routes>
  )
}

export default App
