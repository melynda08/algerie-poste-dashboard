"use client"

import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { BarChart2, FileText, MessageSquare, Upload } from "lucide-react"
import { getUserFiles } from "../services/fileService"
import { getUserHistory } from "../services/historyService"
import { useAuth } from "../contexts/AuthContext"
import { useToast } from "../contexts/ToastContext"

interface FileItem {
  file_id: string
  filename: string
  upload_path: string
}

interface HistoryItem {
  question: string
  response: string
  timestamp: string
  conversation_id: string
  file_id: string
}

const DashboardPage = () => {
  const [files, setFiles] = useState<FileItem[]>([])
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { user } = useAuth()
  const { showToast } = useToast()

  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true)
      try {
        if (user?.user_id) {
          const [filesData, historyData] = await Promise.all([getUserFiles(), getUserHistory(user.user_id, 5)])
          setFiles(filesData)
          setHistory(historyData)
        }
      } catch (error) {
        showToast("Failed to load dashboard data", "error")
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboardData()
  }, [user, showToast])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Quick Stats */}
          <div className="card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <h2 className="text-lg font-semibold mb-2">Files</h2>
            <div className="flex items-center justify-between">
              <span className="text-3xl font-bold">{files.length}</span>
              <FileText size={32} />
            </div>
            <Link to="/files" className="mt-4 inline-block text-sm text-blue-100 hover:text-white">
              Manage Files →
            </Link>
          </div>

          <div className="card bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
            <h2 className="text-lg font-semibold mb-2">Recent Chats</h2>
            <div className="flex items-center justify-between">
              <span className="text-3xl font-bold">{history.length}</span>
              <MessageSquare size={32} />
            </div>
            <Link to="/history" className="mt-4 inline-block text-sm text-emerald-100 hover:text-white">
              View History →
            </Link>
          </div>

          <div className="card bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <h2 className="text-lg font-semibold mb-2">Quick Actions</h2>
            <div className="flex flex-col space-y-2 mt-2">
              <Link
                to="/files"
                className="flex items-center px-3 py-2 bg-white bg-opacity-20 rounded-md hover:bg-opacity-30"
              >
                <Upload size={18} className="mr-2" />
                <span>Upload New File</span>
              </Link>
              <Link
                to="/visualize"
                className="flex items-center px-3 py-2 bg-white bg-opacity-20 rounded-md hover:bg-opacity-30"
              >
                <BarChart2 size={18} className="mr-2" />
                <span>Create Visualization</span>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Recent Files */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Recent Files</h2>
        {files.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Filename
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {files.slice(0, 5).map((file) => (
                  <tr key={file.file_id}>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-900">{file.filename}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                      <Link to={`/chat/${file.file_id}`} className="text-blue-600 hover:text-blue-800 mr-4">
                        Chat
                      </Link>
                      <Link to={`/visualize/${file.file_id}`} className="text-emerald-600 hover:text-emerald-800">
                        Visualize
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-6 text-slate-500">
            <p>No files uploaded yet.</p>
            <Link to="/files" className="mt-2 inline-block text-blue-600 hover:text-blue-800">
              Upload your first file
            </Link>
          </div>
        )}
      </div>

      {/* Recent History */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Recent Conversations</h2>
        {history.length > 0 ? (
          <div className="space-y-4">
            {history.slice(0, 3).map((item, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                <p className="font-medium text-slate-900">{item.question}</p>
                <p className="text-sm text-slate-600 mt-1 line-clamp-2">{item.response}</p>
                <div className="flex justify-between items-center mt-2">
                  <span className="text-xs text-slate-500">{new Date(item.timestamp).toLocaleString()}</span>
                  <Link
                    to={`/chat/${item.file_id}?conversationId=${item.conversation_id}`}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Continue Chat
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-slate-500">
            <p>No conversation history yet.</p>
            <Link to="/chat" className="mt-2 inline-block text-blue-600 hover:text-blue-800">
              Start a new conversation
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

export default DashboardPage
