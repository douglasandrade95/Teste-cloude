import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { AlertTriangle, Clapperboard, Coins, Download, Loader2, Wand2 } from 'lucide-react'

import {
  GenerationCapabilities,
  GenerationModelInfo,
  TaskStatus,
  errorMessage,
  fetchCapabilities,
  fetchCredits,
  fetchTask,
  generateVideo,
} from '../services/api'

const POLL_INTERVAL_MS = 5000

const STATE_LABELS: Record<TaskStatus['state'], string> = {
  waiting: 'Na fila',
  queuing: 'Aguardando vez',
  generating: 'Gerando',
  success: 'Pronto',
  fail: 'Falhou',
}

export function Generate() {
  const [caps, setCaps] = useState<GenerationCapabilities | null>(null)
  const [credits, setCredits] = useState<number | null>(null)
  const [model, setModel] = useState<GenerationModelInfo | null>(null)

  const [prompt, setPrompt] = useState(
    'Aplicação de mega hair tape-in em estúdio no Rio, luz natural de fim de tarde entrando pela janela. Câmera lenta acompanhando o fio caindo, foco raso, textura real do cabelo.'
  )
  const [duration, setDuration] = useState('8')
  const [aspectRatio, setAspectRatio] = useState('9:16')
  const [resolution, setResolution] = useState('720p')

  const [task, setTask] = useState<TaskStatus | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const pollRef = useRef<number | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const loadCredits = useCallback(async () => {
    try {
      setCredits(await fetchCredits())
    } catch {
      setCredits(null)
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    fetchCapabilities()
      .then((data) => {
        if (cancelled) return
        setCaps(data)
        const first = data.models.find((m) => m.implemented) ?? null
        setModel(first)
        if (first) {
          setDuration(first.durations.includes('8') ? '8' : first.durations[0])
          setAspectRatio(first.aspect_ratios.includes('9:16') ? '9:16' : first.aspect_ratios[0])
          setResolution(first.resolutions.includes('720p') ? '720p' : first.resolutions[0])
        }
        if (data.configured) void loadCredits()
      })
      .catch((error) => {
        if (!cancelled) toast.error(errorMessage(error, 'Não consegui carregar os modelos.'))
      })

    return () => {
      cancelled = true
    }
  }, [loadCredits])

  useEffect(() => stopPolling, [stopPolling])

  const startPolling = useCallback(
    (taskId: string) => {
      stopPolling()
      pollRef.current = window.setInterval(async () => {
        try {
          const status = await fetchTask(taskId)
          setTask(status)

          if (status.finished) {
            stopPolling()
            void loadCredits()
            if (status.succeeded) toast.success('Vídeo pronto.')
            else toast.error(status.fail_message || 'A geração falhou.')
          }
        } catch (error) {
          stopPolling()
          toast.error(errorMessage(error, 'Perdi o acompanhamento da tarefa.'))
        }
      }, POLL_INTERVAL_MS)
    },
    [loadCredits, stopPolling]
  )

  const handleGenerate = async () => {
    if (!model) return

    setSubmitting(true)
    setTask(null)
    try {
      const result = await generateVideo({
        model: model.id,
        prompt,
        duration,
        aspect_ratio: aspectRatio,
        resolution,
      })
      toast.success(result.message)
      setTask({
        task_id: result.task_id,
        model: result.model,
        state: 'waiting',
        finished: false,
        succeeded: false,
        progress: 0,
        result_urls: [],
        credits_consumed: null,
        cost_time_ms: null,
        fail_message: '',
      })
      startPolling(result.task_id)
    } catch (error) {
      toast.error(errorMessage(error, 'Não consegui enfileirar a geração.'))
    } finally {
      setSubmitting(false)
    }
  }

  const notConfigured = caps !== null && !caps.configured
  const working = submitting || (task !== null && !task.finished)

  return (
    <div className="min-h-screen bg-ink-950 text-bone-100">
      <div className="mx-auto max-w-3xl px-5 py-14">
        <header className="mb-10 border-b border-white/10 pb-8">
          <p className="mb-3 text-[11px] uppercase tracking-luxe text-gold-400">Geração</p>
          <h1 className="font-display text-5xl font-light text-bone-50">Gerar vídeo</h1>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-bone-300">
            Cada geração consome créditos da sua conta Kie.ai. O pedido é validado
            aqui antes de sair, então erro de parâmetro não custa nada.
          </p>
        </header>

        {notConfigured && (
          <div className="mb-8 flex items-start gap-3 rounded-xl border border-gold-400/30 bg-gold-400/[0.06] px-5 py-4">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-gold-400" />
            <p className="text-sm leading-relaxed text-gold-100">
              Nenhuma chave da Kie.ai configurada. Cadastre uma em{' '}
              <a href="/integracoes" className="underline">
                Integrações
              </a>{' '}
              antes de gerar.
            </p>
          </div>
        )}

        {credits !== null && (
          <div className="mb-8 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-xl border border-white/10 bg-black/30 px-5 py-4">
            <span className="flex items-center gap-2 text-sm text-bone-100">
              <Coins className="h-4 w-4 text-gold-400" />
              <strong className="font-medium tabular-nums">{credits.toFixed(0)}</strong> créditos
            </span>
            <span className="text-xs text-bone-300">
              ≈ US$ {(credits * 0.005).toFixed(2)} pelo preço da Kie.ai
            </span>
          </div>
        )}

        {/* Model */}
        <section className="mb-8">
          <h2 className="mb-3 text-[11px] uppercase tracking-luxe text-bone-300">Modelo</h2>
          <div className="space-y-2">
            {caps?.models.map((option) => {
              const selected = model?.id === option.id
              return (
                <button
                  key={option.id}
                  onClick={() => option.implemented && setModel(option)}
                  disabled={!option.implemented}
                  className={`flex w-full flex-wrap items-center justify-between gap-3 rounded-xl border px-5 py-4 text-left transition ${
                    selected
                      ? 'border-gold-400/60 bg-gold-400/[0.07]'
                      : 'border-white/10 bg-white/[0.02]'
                  } ${option.implemented ? 'hover:border-white/25' : 'cursor-not-allowed opacity-45'}`}
                >
                  <span className="min-w-0">
                    <span className="block font-medium text-bone-50">{option.label}</span>
                    <span className="mt-0.5 block font-mono text-[11px] text-bone-300">
                      {option.id}
                    </span>
                    <span className="mt-1 block text-xs text-bone-300">{option.notes}</span>
                  </span>
                  {!option.implemented && (
                    <span className="rounded-full border border-white/15 px-2 py-0.5 text-[10px] uppercase tracking-widest text-bone-300">
                      Em breve
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        </section>

        {/* Prompt */}
        <section className="mb-8">
          <label
            htmlFor="prompt"
            className="mb-3 block text-[11px] uppercase tracking-luxe text-bone-300"
          >
            Direção da cena
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={5}
            className="w-full rounded-xl border border-white/15 bg-black/40 px-5 py-4 text-sm leading-relaxed text-bone-50 outline-none transition placeholder:text-white/25 focus:border-gold-400/70"
            placeholder="Descreva a cena, a luz, o movimento de câmera e a textura."
          />
        </section>

        {/* Options */}
        {model && (
          <section className="mb-8 grid gap-6 sm:grid-cols-3">
            <OptionGroup
              label="Duração"
              options={model.durations}
              value={duration}
              onChange={setDuration}
              format={(v) => `${v}s`}
            />
            <OptionGroup
              label="Proporção"
              options={model.aspect_ratios}
              value={aspectRatio}
              onChange={setAspectRatio}
            />
            <OptionGroup
              label="Resolução"
              options={model.resolutions}
              value={resolution}
              onChange={setResolution}
            />
          </section>
        )}

        <button
          onClick={handleGenerate}
          disabled={working || !model || !prompt.trim() || notConfigured}
          className="flex items-center gap-2 rounded-xl bg-gold-400 px-7 py-3.5 text-sm font-medium text-ink-950 transition hover:bg-gold-300 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-white/40"
        >
          {working ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Wand2 className="h-4 w-4" />
          )}
          {working ? 'Gerando…' : 'Gerar vídeo'}
        </button>

        {task && <TaskPanel task={task} />}
      </div>
    </div>
  )
}

function OptionGroup({
  label,
  options,
  value,
  onChange,
  format,
}: {
  label: string
  options: string[]
  value: string
  onChange: (value: string) => void
  format?: (value: string) => string
}) {
  return (
    <div>
      <h3 className="mb-3 text-[11px] uppercase tracking-luxe text-bone-300">{label}</h3>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option}
            onClick={() => onChange(option)}
            className={`rounded-lg border px-3.5 py-2 text-xs transition ${
              value === option
                ? 'border-gold-400/60 bg-gold-400/10 text-gold-200'
                : 'border-white/15 text-bone-300 hover:border-white/30 hover:text-bone-100'
            }`}
          >
            {format ? format(option) : option}
          </button>
        ))}
      </div>
    </div>
  )
}

function TaskPanel({ task }: { task: TaskStatus }) {
  const pct = Math.max(0, Math.min(100, Math.round(task.progress)))

  return (
    <section className="mt-10 rounded-2xl border border-white/10 bg-white/[0.02] p-7">
      <div className="mb-5 flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="flex items-center gap-2 font-display text-2xl font-light text-bone-50">
          <Clapperboard className="h-5 w-5 text-gold-400" />
          {STATE_LABELS[task.state] ?? task.state}
        </h2>
        <code className="font-mono text-[11px] text-bone-300">{task.task_id}</code>
      </div>

      {!task.finished && (
        <div className="mb-5">
          <div className="mb-2 flex justify-between text-[10px] uppercase tracking-luxe text-bone-300">
            <span>Progresso</span>
            <span className="tabular-nums text-gold-400">{pct}%</span>
          </div>
          <div className="h-0.5 overflow-hidden rounded bg-white/10">
            <div
              className="h-full bg-gold-400 transition-[width] duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {task.state === 'fail' && (
        <p className="rounded-lg border border-red-400/30 bg-red-400/[0.06] px-4 py-3 text-sm text-red-200">
          {task.fail_message || 'A geração falhou sem detalhe.'}
        </p>
      )}

      {task.result_urls.map((url) => (
        <div key={url} className="mb-4 space-y-3">
          <video
            src={url}
            controls
            playsInline
            className="w-full rounded-xl border border-white/10 bg-black"
          />
          <a
            href={url}
            target="_blank"
            rel="noreferrer noopener"
            className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-4 py-2.5 text-xs uppercase tracking-widest text-bone-200 transition hover:border-gold-400/60 hover:text-gold-200"
          >
            <Download className="h-3.5 w-3.5" />
            Abrir o arquivo
          </a>
        </div>
      ))}

      {task.finished && (
        <dl className="mt-5 flex flex-wrap gap-x-8 gap-y-2 border-t border-white/10 pt-5 text-xs text-bone-300">
          {task.credits_consumed !== null && (
            <div>
              <dt className="inline uppercase tracking-widest">Créditos </dt>
              <dd className="inline tabular-nums text-bone-100">{task.credits_consumed}</dd>
            </div>
          )}
          {task.cost_time_ms !== null && (
            <div>
              <dt className="inline uppercase tracking-widest">Tempo </dt>
              <dd className="inline tabular-nums text-bone-100">
                {(task.cost_time_ms / 1000).toFixed(1)}s
              </dd>
            </div>
          )}
        </dl>
      )}
    </section>
  )
}
