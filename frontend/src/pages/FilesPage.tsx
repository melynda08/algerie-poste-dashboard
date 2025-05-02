"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Link } from "react-router-dom"
import { Upload, FileText, Trash2, MessageSquare, BarChart2 } from "lucide-react"
import { getUserFiles, uploadFile, deleteFile } from "../services/fileService"
import { useToast } from "../contexts/ToastContext"

interface FileItem {
  file_id: string
  filename: string
  upload_path: string
}

const FilesPage = () => {
  const [files, setFiles] = useState<FileItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { showToast } = useToast()

  useEffect(() => {
    fetchFiles()
  }, [])

  const fetchFiles = async () => {
    setIsLoading(true)
    try {
      const filesData = await getUserFiles()
      setFiles(filesData)
    } catch (error) {
      showToast("Failed to load files", "error")
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return

    const file = e.target.files[0]
    if (!file.name.endsWith(".csv")) {
      showToast("Only CSV files are supported", "error")
      return
    }

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append("file", file)

      await uploadFile(formData)
      showToast("File uploaded successfully", "success")
      fetchFiles()
    } catch (error) {
      showToast("Failed to upload file", "error")
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  const handleDeleteFile = async (fileId: string, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete ${filename}?`)) {
      return
    }

    try {
      await deleteFile(fileId)
      showToast("File deleted successfully", "success")
      setFiles(files.filter((file) => file.file_id !== fileId))
    } catch (error) {
      showToast("Failed to delete file", "error")
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Files</h1>
        <div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".csv"
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className={`btn btn-primary flex items-center ${isUploading ? "opacity-70 cursor-not-allowed" : ""}`}
          >
            <Upload size={18} className="mr-2" />
            {isUploading ? "Uploading..." : "Upload CSV"}
          </label>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="card">
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
                  {files.map((file) => (
                    <tr key={file.file_id}>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <FileText size={20} className="text-slate-400 mr-3" />
                          <span className="text-sm text-slate-900">{file.filename}</span>
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Link
                          to={`/chat/${file.file_id}`}
                          className="text-blue-600 hover:text-blue-800 inline-flex items-center mr-4"
                        >
                          <MessageSquare size={16} className="mr-1" />
                          Chat
                        </Link>
                        <Link
                          to={`/visualize/${file.file_id}`}
                          className="text-emerald-600 hover:text-emerald-800 inline-flex items-center mr-4"
                        >
                          <BarChart2 size={16} className="mr-1" />
                          Visualize
                        </Link>
                        <button
                          onClick={() => handleDeleteFile(file.file_id, file.filename)}
                          className="text-red-600 hover:text-red-800 inline-flex items-center"
                        >
                          <Trash2 size={16} className="mr-1" />
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText size={48} className="mx-auto text-slate-300" />
              <h3 className="mt-4 text-lg font-medium text-slate-900">No files uploaded</h3>
              <p className="mt-1 text-sm text-slate-500">Upload a CSV file to get started</p>
              <div className="mt-6">
                <label htmlFor="file-upload" className="btn btn-primary inline-flex items-center">
                  <Upload size={18} className="mr-2" />
                  Upload CSV
                </label>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default FilesPage
