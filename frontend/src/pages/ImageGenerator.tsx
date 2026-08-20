import { useState, useRef, useEffect } from 'react'
import { Sparkles, Wand2 } from 'lucide-react'
import toast from 'react-hot-toast'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type JobStatus = 'idle' | 'queued' | 'in_progress' | 'completed' | 'error'

export function ImageGenerator() {
  const [prompt, setPrompt] = useState('')
  const [requestId, setRequestId] = useState<string | null>(null)
  const [status, setStatus] = useState<JobStatus>('idle')
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Digite um prompt')
      return
    }

    setStatus('queued')
    setImageUrl(null)

    try {
      const response = await axios.post(`${API_URL}/api/v1/fal/generate`, {
        prompt,
      })

      const id = response.data.request_id
      setRequestId(id)
      toast.success('Geração enfileirada')

      pollRef.current = setInterval(async () => {
        try {
          const statusResponse = await axios.get(
            `${API_URL}/api/v1/fal/status/${id}`
          )
          const jobStatus = statusResponse.data.status

          if (jobStatus === 'COMPLETED') {
            if (pollRef.current) clearInterval(pollRef.current)
            const resultResponse = await axios.get(
              `${API_URL}/api/v1/fal/result/${id}`
            )
            const url = resultResponse.data?.images?.[0]?.url
            setImageUrl(url ?? null)
            setStatus('completed')
            toast.success('Imagem gerada!')
          } else if (jobStatus === 'IN_PROGRESS') {
            setStatus('in_progress')
          }
        } catch (error) {
          if (pollRef.current) clearInterval(pollRef.current)
          setStatus('error')
          toast.error('Erro ao consultar status')
          console.error(error)
        }
      }, 2000)
    } catch (error) {
      setStatus('error')
      toast.error('Falha ao iniciar geração')
      console.error(error)
    }
  }

  const isBusy = status === 'queued' || status === 'in_progress'

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Wand2 className="w-8 h-8 text-purple-400" />
            <h1 className="text-4xl font-bold text-white">Gerador de Imagens</h1>
            <Sparkles className="w-8 h-8 text-purple-400" />
          </div>
          <p className="text-lg text-slate-400">
            Powered by fal.ai (nano-banana-2)
          </p>
        </div>

        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 backdrop-blur space-y-6">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isBusy}
            placeholder="Descreva a imagem que você quer gerar..."
            rows={4}
            className="w-full bg-slate-900/60 border border-slate-700 rounded-xl p-4 text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 resize-none"
          />

          <button
            onClick={handleGenerate}
            disabled={isBusy || !prompt.trim()}
            className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 text-white font-bold py-3 px-6 rounded-xl transition flex items-center justify-center gap-2"
          >
            <Wand2 className="w-5 h-5" />
            {status === 'queued' && 'Enfileirando...'}
            {status === 'in_progress' && 'Gerando...'}
            {(status === 'idle' || status === 'completed' || status === 'error') &&
              'Gerar Imagem'}
          </button>

          {requestId && (
            <p className="text-xs text-slate-500 text-center break-all">
              request_id: {requestId}
            </p>
          )}

          {status === 'completed' && imageUrl && (
            <div className="pt-4">
              <img
                src={imageUrl}
                alt={prompt}
                className="w-full rounded-xl border border-slate-700"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
