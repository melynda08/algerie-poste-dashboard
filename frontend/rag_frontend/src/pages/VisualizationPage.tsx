"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { BarChart2, FileText, Download, PlusCircle } from "lucide-react"
import { getUserFiles } from "../services/fileService"
import { generateVisualization } from "../services/visualizationService"
import { addVisualizationToDashboard } from "../services/dashboardService"
import { useToast } from "../contexts/ToastContext"

interface FileItem {
  file_id: string
  filename: string
}

const VisualizationPage = () => {
  const { fileId } = useParams<{ fileId?: string }>()
  const [files, setFiles] = useState<FileItem[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(fileId || null)
  const [selectedFileName, setSelectedFileName] = useState<string>("")
  const [prompt, setPrompt] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [visualization, setVisualization] = useState<string | null>(null)
  const [visualizationTitle, setVisualizationTitle] = useState<string>("")
  const [chartType, setChartType] = useState<string>("")
  const [isAddingToDashboard, setIsAddingToDashboard] = useState(false)

  const { showToast } = useToast()
  const navigate = useNavigate()

  useEffect(() => {
    fetchFiles()
  }, [])

  useEffect(() => {
    if (fileId && fileId !== selectedFile) {
      setSelectedFile(fileId)
    }
  }, [fileId])

  useEffect(() => {
    if (selectedFile) {
      const file = files.find((f) => f.file_id === selectedFile)
      if (file) {
        setSelectedFileName(file.filename)
      }
    }
  }, [selectedFile, files])

  const fetchFiles = async () => {
    try {
      const filesData = await getUserFiles()
      setFiles(filesData)

      if (filesData.length > 0 && !selectedFile) {
        setSelectedFile(filesData[0].file_id)
      }
    } catch (error) {
      showToast("Failed to load files", "error")
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newFileId = e.target.value
    setSelectedFile(newFileId)
    setVisualization(null)
    navigate(`/visualize/${newFileId}`)
  }

  const handleGenerateVisualization = async () => {
    if (!selectedFile) return

    setIsLoading(true)
    try {
      const response = await generateVisualization({
        file_id: selectedFile,
        prompt: prompt || undefined,
      })

      setVisualization(response.image)
      setVisualizationTitle(response.title || "Data Visualization")
      setChartType(response.chart_type || "")
      showToast("Visualization generated successfully", "success")
    } catch (error) {
      showToast("Failed to generate visualization", "error")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = () => {
    if (!visualization) return

    // Create a temporary link to download the image
    const link = document.createElement("a")
    link.href = visualization
    link.download = `${selectedFileName.replace(".csv", "")}_${chartType}_visualization.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleAddToDashboard = async () => {
    if (!visualization || !selectedFile) return

    setIsAddingToDashboard(true)
    try {
      await addVisualizationToDashboard({
        title: visualizationTitle,
        image: visualization,
        chart_type: chartType,
        prompt: prompt,
        file_id: selectedFile,
        file_name: selectedFileName,
      })

      showToast("Visualization added to dashboard successfully", "success")
    } catch (error) {
      showToast("Failed to add visualization to dashboard", "error")
    } finally {
      setIsAddingToDashboard(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Visualize Data</h1>
      </div>

      <div className="card">
        <div className="flex flex-col md:flex-row md:items-end gap-4 mb-6">
          <div className="flex-1">
            <label htmlFor="file-select" className="label">
              Select CSV File
            </label>
            <div className="relative">
              <select
                id="file-select"
                value={selectedFile || ""}
                onChange={handleFileChange}
                className="input py-2 pr-8 pl-3"
              >
                <option value="" disabled>
                  Select a file
                </option>
                {files.map((file) => (
                  <option key={file.file_id} value={file.file_id}>
                    {file.filename}
                  </option>
                ))}
              </select>
              <FileText
                size={16}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-500 pointer-events-none"
              />
            </div>
          </div>

          <div className="flex-1">
            <label htmlFor="visualization-prompt" className="label">
              Visualization Prompt (Optional)
            </label>
            <div className="flex">
              <input
                id="visualization-prompt"
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., Show me a bar chart of top categories"
                className="input flex-1"
              />
              <button
                onClick={handleGenerateVisualization}
                disabled={isLoading || !selectedFile}
                className={`ml-3 btn ${
                  isLoading || !selectedFile ? "bg-slate-300 text-slate-500 cursor-not-allowed" : "btn-primary"
                }`}
              >
                {isLoading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    <span>Generating...</span>
                  </div>
                ) : (
                  <>
                    <BarChart2 size={18} className="mr-2" />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="bg-slate-50 rounded-lg border border-slate-200 p-4 min-h-[400px] flex items-center justify-center">
          {visualization ? (
            <div className="w-full">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-slate-900">{visualizationTitle}</h3>
                <div className="flex gap-2">
                  <button
                    onClick={handleAddToDashboard}
                    disabled={isAddingToDashboard}
                    className="btn btn-primary flex items-center"
                  >
                    {isAddingToDashboard ? (
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        <span>Adding...</span>
                      </div>
                    ) : (
                      <>
                        <PlusCircle size={16} className="mr-2" />
                        Add to Dashboard
                      </>
                    )}
                  </button>
                  <button onClick={handleDownload} className="btn btn-secondary flex items-center">
                    <Download size={16} className="mr-2" />
                    Download
                  </button>
                </div>
              </div>
              <div className="flex justify-center">
                <img
                  src={visualization || "/placeholder.svg"}
                  alt={visualizationTitle}
                  className="max-w-full max-h-[500px] object-contain"
                />
              </div>
            </div>
          ) : (
            <div className="text-center p-6">
              <BarChart2 size={48} className="mx-auto text-slate-300" />
              <h3 className="mt-4 text-lg font-medium text-slate-900">No visualization yet</h3>
              <p className="mt-1 text-sm text-slate-500">
                {selectedFile ? 'Click "Generate" to create a visualization' : "Please select a CSV file to visualize"}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default VisualizationPage
