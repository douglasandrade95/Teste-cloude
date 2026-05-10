import { useState } from 'react'
import { Upload, Sparkles, Play } from 'lucide-react'
import toast from 'react-hot-toast'
import axios from 'axios'

interface Analysis {
  primary_emotion: string
  secondary_emotions: string[]
  intensity: number
  recommended_pacing: string
  color_temperature: string
  suggested_music_mood: string
}

export function Editor() {
  const [file, setFile] = useState<File | null>(null)
  const [vibe, setVibe] = useState('luxury')
  const [loading, setLoading] = useState(false)
  const [projectId, setProjectId] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [editingProgress, setEditingProgress] = useState(0)

  const vibeOptions = [
    { value: 'luxury', label: '💎 Luxury' },
    { value: 'energy', label: '⚡ Energy' },
    { value: 'elegance', label: '✨ Elegance' },
    { value: 'drama', label: '🎭 Drama' },
    { value: 'humor', label: '😄 Humor' },
    { value: 'mystery', label: '🌙 Mystery' },
    { value: 'sensuality', label: '💃 Sensuality' },
    { value: 'authority', label: '👑 Authority' },
    { value: 'lifestyle', label: '🏖️ Lifestyle' },
    { value: 'acolhimento', label: '🤗 Acolhimento' },
  ]

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select a video')
      return
    }

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('vibe', vibe)
    formData.append('description', 'Auto-edited video')

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/upload',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      )

      setProjectId(response.data.project_id)
      setAnalysis(response.data.emotional_analysis)
      toast.success('Video uploaded! Analysis complete.')
    } catch (error) {
      toast.error('Upload failed')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleStartEditing = async () => {
    if (!projectId) return

    setLoading(true)
    try {
      await axios.post(`http://localhost:8000/api/v1/edit/${projectId}`)
      toast.success('Editing started!')

      // Poll for progress
      const interval = setInterval(async () => {
        const response = await axios.get(
          `http://localhost:8000/api/v1/edit/${projectId}/status`
        )
        setEditingProgress(response.data.progress)

        if (response.data.status === 'completed') {
          clearInterval(interval)
          toast.success('Video edited successfully!')
          setLoading(false)
        }
      }, 2000)
    } catch (error) {
      toast.error('Failed to start editing')
      console.error(error)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-8 h-8 text-blue-400" />
            <h1 className="text-4xl font-bold text-white">AutoVideoEditor</h1>
            <Sparkles className="w-8 h-8 text-blue-400" />
          </div>
          <p className="text-lg text-slate-400">
            Transforme vídeos comuns em conteúdo cinematográfico premium
          </p>
        </div>

        <div className="space-y-8">
          {/* Upload Section */}
          {!projectId && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 backdrop-blur">
              <h2 className="text-2xl font-bold text-white mb-6">
                1. Escolha seu vídeo
              </h2>

              <div className="mb-6">
                <label className="block w-full border-2 border-dashed border-slate-600 rounded-xl p-8 text-center cursor-pointer hover:border-blue-500 transition">
                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleFileChange}
                    disabled={loading}
                    className="hidden"
                  />
                  <Upload className="w-12 h-12 mx-auto mb-2 text-slate-400" />
                  <p className="text-slate-300">
                    {file ? file.name : 'Clique para fazer upload do seu vídeo'}
                  </p>
                  <p className="text-sm text-slate-500 mt-1">
                    MP4, MOV, AVI (máx 5GB)
                  </p>
                </label>
              </div>

              {/* Vibe Selection */}
              <h3 className="text-lg font-semibold text-white mb-4">
                2. Escolha a atmosfera
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
                {vibeOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setVibe(option.value)}
                    className={`p-3 rounded-lg font-medium transition ${
                      vibe === option.value
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>

              {/* Upload Button */}
              <button
                onClick={handleUpload}
                disabled={!file || loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white font-bold py-3 px-6 rounded-xl transition"
              >
                {loading ? 'Analisando...' : 'Analisar Vídeo'}
              </button>
            </div>
          )}

          {/* Analysis Results */}
          {analysis && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 backdrop-blur">
              <h2 className="text-2xl font-bold text-white mb-6">
                Análise Emocional
              </h2>

              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Emoção Principal</p>
                  <p className="text-2xl font-bold text-blue-400">
                    {analysis.primary_emotion}
                  </p>
                </div>

                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Intensidade</p>
                  <p className="text-2xl font-bold text-blue-400">
                    {(analysis.intensity * 100).toFixed(0)}%
                  </p>
                </div>

                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Ritmo Recomendado</p>
                  <p className="text-xl font-bold text-blue-400">
                    {analysis.recommended_pacing}
                  </p>
                </div>

                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Temperatura de Cor</p>
                  <p className="text-xl font-bold text-blue-400">
                    {analysis.color_temperature}
                  </p>
                </div>
              </div>

              <button
                onClick={handleStartEditing}
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-slate-700 text-white font-bold py-3 px-6 rounded-xl transition flex items-center justify-center gap-2"
              >
                <Play className="w-5 h-5" />
                {loading ? `Editando... ${editingProgress}%` : 'Começar Edição'}
              </button>
            </div>
          )}

          {/* Download Section */}
          {projectId && editingProgress === 100 && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 backdrop-blur text-center">
              <h2 className="text-2xl font-bold text-white mb-4">
                ✨ Vídeo Pronto!
              </h2>
              <p className="text-slate-300 mb-6">
                Seu vídeo foi editado com sucesso
              </p>
              <a
                href={`http://localhost:8000/api/v1/download/${projectId}`}
                className="inline-block bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-8 rounded-xl transition"
              >
                Baixar Vídeo
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
