"use client"

import { useState, useEffect } from "react"
import { Settings, Database, Cpu } from "lucide-react"
import { getEmbeddingModels, setEmbeddingProvider } from "../services/settingsService"
import { useToast } from "../contexts/ToastContext"

interface EmbeddingModelsResponse {
  current_provider: string
  current_model: string
  local_models: string[]
  together_models: string[]
  huggingface_models: string[]
}

const SettingsPage = () => {
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [embeddingModels, setEmbeddingModels] = useState<EmbeddingModelsResponse | null>(null)
  const [selectedProvider, setSelectedProvider] = useState("local")
  const [selectedModel, setSelectedModel] = useState("")
  const { showToast } = useToast()

  useEffect(() => {
    fetchEmbeddingModels()
  }, [])

  useEffect(() => {
    if (embeddingModels) {
      setSelectedProvider(embeddingModels.current_provider)
      setSelectedModel(embeddingModels.current_model)
    }
  }, [embeddingModels])

  const fetchEmbeddingModels = async () => {
    setIsLoading(true)
    try {
      const data = await getEmbeddingModels()
      setEmbeddingModels(data)
    } catch (error) {
      showToast("Failed to load embedding models", "error")
    } finally {
      setIsLoading(false)
    }
  }

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider)

    // Set default model for the selected provider
    if (embeddingModels) {
      if (provider === "local" && embeddingModels.local_models.length > 0) {
        setSelectedModel(embeddingModels.local_models[0])
      } else if (provider === "together" && embeddingModels.together_models.length > 0) {
        setSelectedModel(embeddingModels.together_models[0])
      } else if (provider === "huggingface" && embeddingModels.huggingface_models.length > 0) {
        setSelectedModel(embeddingModels.huggingface_models[0])
      } else {
        setSelectedModel("")
      }
    }
  }

  const handleSaveSettings = async () => {
    setIsSaving(true)
    try {
      await setEmbeddingProvider({
        provider: selectedProvider,
        model: selectedModel,
      })
      showToast("Embedding settings saved successfully", "success")
    } catch (error) {
      showToast("Failed to save embedding settings", "error")
    } finally {
      setIsSaving(false)
    }
  }

  const getAvailableModels = () => {
    if (!embeddingModels) return []

    switch (selectedProvider) {
      case "local":
        return embeddingModels.local_models
      case "together":
        return embeddingModels.together_models
      case "huggingface":
        return embeddingModels.huggingface_models
      case "openai":
        return ["text-embedding-3-small", "text-embedding-3-large"]
      default:
        return []
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Settings</h1>

      <div className="card">
        <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center">
          <Cpu size={20} className="mr-2" />
          Embedding Settings
        </h2>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <div className="space-y-6">
            <div>
              <label className="label">Embedding Provider</label>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <button
                  onClick={() => handleProviderChange("local")}
                  className={`p-4 border rounded-md flex flex-col items-center ${
                    selectedProvider === "local"
                      ? "border-blue-500 bg-blue-50 text-blue-700"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Cpu size={24} className="mb-2" />
                  <span className="font-medium">Local</span>
                  <span className="text-xs text-slate-500 mt-1">Sentence Transformers</span>
                </button>

                <button
                  onClick={() => handleProviderChange("openai")}
                  className={`p-4 border rounded-md flex flex-col items-center ${
                    selectedProvider === "openai"
                      ? "border-blue-500 bg-blue-50 text-blue-700"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Database size={24} className="mb-2" />
                  <span className="font-medium">OpenAI</span>
                  <span className="text-xs text-slate-500 mt-1">API Key Required</span>
                </button>

                <button
                  onClick={() => handleProviderChange("together")}
                  className={`p-4 border rounded-md flex flex-col items-center ${
                    selectedProvider === "together"
                      ? "border-blue-500 bg-blue-50 text-blue-700"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Database size={24} className="mb-2" />
                  <span className="font-medium">Together AI</span>
                  <span className="text-xs text-slate-500 mt-1">API Key Required</span>
                </button>

                <button
                  onClick={() => handleProviderChange("huggingface")}
                  className={`p-4 border rounded-md flex flex-col items-center ${
                    selectedProvider === "huggingface"
                      ? "border-blue-500 bg-blue-50 text-blue-700"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Database size={24} className="mb-2" />
                  <span className="font-medium">Hugging Face</span>
                  <span className="text-xs text-slate-500 mt-1">API Key Required</span>
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="model-select" className="label">
                Embedding Model
              </label>
              <select
                id="model-select"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="input"
              >
                <option value="" disabled>
                  Select a model
                </option>
                {getAvailableModels().map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <p className="text-sm text-slate-500 mt-1">
                {selectedProvider === "local"
                  ? "Local models run on your server without API calls"
                  : `${selectedProvider.charAt(0).toUpperCase() + selectedProvider.slice(1)} requires an API key in your .env file`}
              </p>
            </div>

            <div className="pt-4 border-t border-slate-200">
              <button
                onClick={handleSaveSettings}
                disabled={isSaving || !selectedModel}
                className={`btn ${
                  isSaving || !selectedModel ? "bg-slate-300 text-slate-500 cursor-not-allowed" : "btn-primary"
                }`}
              >
                {isSaving ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    <span>Saving...</span>
                  </div>
                ) : (
                  <>
                    <Settings size={18} className="mr-2" />
                    Save Settings
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default SettingsPage
