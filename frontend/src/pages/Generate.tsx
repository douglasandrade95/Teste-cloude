import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import {
  AlertTriangle,
  Clapperboard,
  Coins,
  Download,
  ExternalLink,
  Loader2,
  Search,
  Wand2,
} from 'lucide-react'

import {
  FieldSpec,
  ModelSpec,
  TaskStatus,
  errorMessage,
  fetchCatalog,
  fetchCredits,
  fetchDownloadUrl,
  fetchTask,
  generateVideo,
} from '../services/api'

const POLL_INTERVAL_MS = 5000

const STATE_LABELS: Record<string, string> = {
  waiting: 'Na fila',
  queuing: 'Aguardando vez',
  generating: 'Gerando',
  success: 'Pronto',
  fail: 'Falhou',
}

/** Friendly names for the provider's parameter keys. Unlisted keys show raw. */
const FIELD_LABELS: Record<string, string> = {
  prompt: 'Direção da cena',
  duration: 'Duração',
  aspect_ratio: 'Proporção',
  resolution: 'Resolução',
  seed: 'Seed',
  generate_audio: 'Gerar áudio',
  audio: 'Áudio',
  output_format: 'Formato',
  first_frame_url: 'Primeiro quadro (URL)',
  last_frame_url: 'Último quadro (URL)',
  image_urls: 'Imagens de referência',
  reference_image_urls: 'Imagens de referência',
  reference_video_urls: 'Vídeos de referência',
  reference_audio_urls: 'Áudios de referência',
  reference_file_urls: 'Arquivos de referência',
  reference_link_urls: 'Links de referência',
  character_ids: 'Personagens',
  audio_ids: 'Áudios',
  nsfw_checker: 'Filtro de conteúdo',
  web_search: 'Busca na web',
  return_last_frame: 'Devolver último quadro',
}

function labelFor(field: FieldSpec): string {
  return FIELD_LABELS[field.name] ?? field.name.replace(/_/g, ' ')
}

/** Long free text gets a textarea; short strings an input. */
function isLongText(field: FieldSpec): boolean {
  return field.type === 'string' && (field.max_length ?? 0) > 500
}

export function Generate() {
  const [models, setModels] = useState<ModelSpec[]>([])
  const [categories, setCategories] = useState<{ id: string; label: string }[]>([])
  const [configured, setConfigured] = useState(true)
  const [loading, setLoading] = useState(true)

  const [selected, setSelected] = useState<ModelSpec | null>(null)
  const [values, setValues] = useState<Record<string, unknown>>({})
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<string>('todos')

  const [credits, setCredits] = useState<number | null>(null)
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

  /** Seed the form from the model's own declared defaults. */
  const selectModel = useCallback((model: ModelSpec) => {
    setSelected(model)
    setTask(null)
    const defaults: Record<string, unknown> = {}
    model.fields.forEach((field) => {
      if (field.default !== null && field.default !== undefined) {
        defaults[field.name] = field.default
      }
    })
    setValues(defaults)
  }, [])

  useEffect(() => {
    let cancelled = false

    fetchCatalog()
      .then((data) => {
        if (cancelled) return
        setModels(data.models)
        setCategories(data.categories)
        setConfigured(data.configured)
        if (data.models[0]) selectModel(data.models[0])
        if (data.configured) void loadCredits()
      })
      .catch((error) => {
        if (!cancelled) toast.error(errorMessage(error, 'Não consegui carregar o catálogo.'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [loadCredits, selectModel])

  useEffect(() => stopPolling, [stopPolling])

  const visibleModels = useMemo(() => {
    const term = search.trim().toLowerCase()
    return models.filter((model) => {
      const matchesCategory = category === 'todos' || model.category === category
      const matchesTerm =
        !term ||
        model.label.toLowerCase().includes(term) ||
        model.id.toLowerCase().includes(term)
      return matchesCategory && matchesTerm
    })
  }, [models, search, category])

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
    if (!selected) return
    setSubmitting(true)
    setTask(null)
    try {
      const result = await generateVideo({ model: selected.id, values })
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

  const setValue = (name: string, value: unknown) =>
    setValues((current) => ({ ...current, [name]: value }))

  const working = submitting || (task !== null && !task.finished)
  const promptField = selected?.fields.find((f) => f.name === 'prompt')
  const otherFields = selected?.fields.filter((f) => f.name !== 'prompt') ?? []

  return (
    <div className="min-h-screen bg-ink-950 text-bone-100">
      <div className="mx-auto max-w-5xl px-5 py-14">
        <header className="mb-10 border-b border-white/10 pb-8">
          <p className="mb-3 text-[11px] uppercase tracking-luxe text-gold-400">Geração</p>
          <h1 className="font-display text-5xl font-light text-bone-50">Studio</h1>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-bone-300">
            Os controles abaixo pertencem ao modelo selecionado — eles vêm do
            schema publicado pela Kie.ai, não de código escrito à mão. Cada
            geração é cobrada no seu saldo.
          </p>
        </header>

        {!configured && (
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
            <span className="flex items-center gap-2 text-sm">
              <Coins className="h-4 w-4 text-gold-400" />
              <strong className="font-medium tabular-nums">{credits.toFixed(0)}</strong> créditos
            </span>
            <span className="text-xs text-bone-300">
              ≈ US$ {(credits * 0.005).toFixed(2)}
            </span>
          </div>
        )}

        {loading ? (
          <p className="flex items-center gap-3 py-20 text-bone-300">
            <Loader2 className="h-5 w-5 animate-spin text-gold-400" />
            Carregando catálogo…
          </p>
        ) : (
          <div className="grid gap-8 lg:grid-cols-[280px_1fr]">
            {/* Catalog */}
            <aside>
              <div className="relative mb-3">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-bone-300" />
                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Buscar modelo"
                  aria-label="Buscar modelo"
                  className="w-full rounded-lg border border-white/15 bg-black/40 py-2.5 pl-9 pr-3 text-sm outline-none transition placeholder:text-white/25 focus:border-gold-400/70"
                />
              </div>

              <div className="mb-4 flex flex-wrap gap-1.5">
                {[{ id: 'todos', label: 'Todos' }, ...categories].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setCategory(item.id)}
                    className={`rounded-full border px-3 py-1 text-[11px] transition ${
                      category === item.id
                        ? 'border-gold-400/60 bg-gold-400/10 text-gold-200'
                        : 'border-white/15 text-bone-300 hover:text-bone-100'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              <div className="space-y-2">
                {visibleModels.map((model) => (
                  <button
                    key={model.id}
                    onClick={() => selectModel(model)}
                    className={`w-full rounded-xl border px-4 py-3 text-left transition ${
                      selected?.id === model.id
                        ? 'border-gold-400/60 bg-gold-400/[0.07]'
                        : 'border-white/10 bg-white/[0.02] hover:border-white/25'
                    }`}
                  >
                    <span className="block text-sm font-medium text-bone-50">{model.label}</span>
                    <span className="mt-0.5 block font-mono text-[10px] text-bone-300">
                      {model.id}
                    </span>
                    <span className="mt-1 block text-[11px] text-bone-300">
                      {model.category_label} · {model.fields.length} parâmetros
                    </span>
                  </button>
                ))}
                {visibleModels.length === 0 && (
                  <p className="px-1 py-4 text-xs text-bone-300">Nenhum modelo com esse termo.</p>
                )}
              </div>
            </aside>

            {/* Parameters */}
            <section>
              {selected ? (
                <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-7">
                  <div className="mb-6 flex flex-wrap items-baseline justify-between gap-3">
                    <h2 className="font-display text-3xl font-light text-bone-50">
                      {selected.label}
                    </h2>
                    {selected.docs_url && (
                      <a
                        href={selected.docs_url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="flex items-center gap-1.5 text-xs text-gold-400 hover:text-gold-300"
                      >
                        Schema do modelo
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>

                  {promptField && (
                    <div className="mb-7">
                      <FieldControl
                        field={promptField}
                        value={values[promptField.name]}
                        onChange={(v) => setValue(promptField.name, v)}
                      />
                    </div>
                  )}

                  <div className="grid gap-6 sm:grid-cols-2">
                    {otherFields.map((field) => (
                      <FieldControl
                        key={field.name}
                        field={field}
                        value={values[field.name]}
                        onChange={(v) => setValue(field.name, v)}
                      />
                    ))}
                  </div>

                  <button
                    onClick={handleGenerate}
                    disabled={working || !configured}
                    className="mt-8 flex items-center gap-2 rounded-xl bg-gold-400 px-7 py-3.5 text-sm font-medium text-ink-950 transition hover:bg-gold-300 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-white/40"
                  >
                    {working ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Wand2 className="h-4 w-4" />
                    )}
                    {working ? 'Gerando…' : 'Gerar vídeo'}
                  </button>
                </div>
              ) : (
                <p className="text-bone-300">Selecione um modelo.</p>
              )}

              {task && <TaskPanel task={task} />}
            </section>
          </div>
        )}
      </div>
    </div>
  )
}

/** Renders one control, chosen from the field's published type. */
function FieldControl({
  field,
  value,
  onChange,
}: {
  field: FieldSpec
  value: unknown
  onChange: (value: unknown) => void
}) {
  const label = labelFor(field)
  const inputId = `field-${field.name}`

  const header = (
    <div className="mb-2 flex flex-wrap items-baseline gap-2">
      <label htmlFor={inputId} className="text-[11px] uppercase tracking-luxe text-bone-300">
        {label}
      </label>
      {field.required && <span className="text-[10px] text-gold-400">obrigatório</span>}
    </div>
  )

  const hint = field.description ? (
    <p className="mt-1.5 text-[11px] leading-relaxed text-bone-300/70">
      {field.description.length > 160
        ? `${field.description.slice(0, 160)}…`
        : field.description}
    </p>
  ) : null

  // Enum -> chips
  if (field.enum && field.enum.length > 0) {
    return (
      <div>
        {header}
        <div className="flex flex-wrap gap-2">
          {field.enum.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => onChange(option)}
              className={`rounded-lg border px-3.5 py-2 text-xs transition ${
                String(value) === option
                  ? 'border-gold-400/60 bg-gold-400/10 text-gold-200'
                  : 'border-white/15 text-bone-300 hover:border-white/30 hover:text-bone-100'
              }`}
            >
              {option}
            </button>
          ))}
        </div>
        {hint}
      </div>
    )
  }

  // Boolean -> two-state switch
  if (field.type === 'boolean') {
    const on = value === true
    return (
      <div>
        {header}
        <button
          id={inputId}
          type="button"
          role="switch"
          aria-checked={on}
          onClick={() => onChange(!on)}
          className={`flex h-8 w-14 items-center rounded-full border px-1 transition ${
            on ? 'border-gold-400/60 bg-gold-400/20' : 'border-white/15 bg-black/40'
          }`}
        >
          <span
            className={`h-5 w-5 rounded-full transition-transform ${
              on ? 'translate-x-6 bg-gold-400' : 'translate-x-0 bg-white/30'
            }`}
          />
        </button>
        {hint}
      </div>
    )
  }

  // Numbers
  if (field.type === 'integer' || field.type === 'number') {
    return (
      <div>
        {header}
        <input
          id={inputId}
          type="number"
          value={value === undefined || value === null ? '' : String(value)}
          min={field.minimum ?? undefined}
          max={field.maximum ?? undefined}
          step={field.type === 'integer' ? 1 : 'any'}
          onChange={(e) =>
            onChange(e.target.value === '' ? undefined : Number(e.target.value))
          }
          className="w-full rounded-xl border border-white/15 bg-black/40 px-4 py-3 text-sm tabular-nums outline-none transition focus:border-gold-400/70"
        />
        {hint}
      </div>
    )
  }

  // Arrays of URLs/ids -> one per line
  if (field.type === 'array') {
    const lines = Array.isArray(value) ? (value as unknown[]).join('\n') : ''
    return (
      <div>
        {header}
        <textarea
          id={inputId}
          value={lines}
          rows={3}
          placeholder={'um por linha'}
          onChange={(e) =>
            onChange(
              e.target.value
                .split('\n')
                .map((line) => line.trim())
                .filter(Boolean)
            )
          }
          className="w-full rounded-xl border border-white/15 bg-black/40 px-4 py-3 font-mono text-xs outline-none transition placeholder:text-white/25 focus:border-gold-400/70"
        />
        {field.max_items && (
          <p className="mt-1.5 text-[11px] text-bone-300/70">Até {field.max_items}.</p>
        )}
        {hint}
      </div>
    )
  }

  // Long free text -> textarea; short -> input
  if (isLongText(field)) {
    return (
      <div>
        {header}
        <textarea
          id={inputId}
          value={typeof value === 'string' ? value : ''}
          rows={5}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Descreva a cena, a luz, o movimento de câmera e a textura."
          className="w-full rounded-xl border border-white/15 bg-black/40 px-5 py-4 text-sm leading-relaxed outline-none transition placeholder:text-white/25 focus:border-gold-400/70"
        />
        {field.max_length && (
          <p className="mt-1.5 text-[11px] text-bone-300/70">
            {typeof value === 'string' ? value.length : 0} / {field.max_length}
          </p>
        )}
      </div>
    )
  }

  return (
    <div>
      {header}
      <input
        id={inputId}
        type="text"
        value={typeof value === 'string' ? value : ''}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-white/15 bg-black/40 px-4 py-3 text-sm outline-none transition focus:border-gold-400/70"
      />
      {hint}
    </div>
  )
}

function ResultVideo({ url }: { url: string }) {
  const [fetching, setFetching] = useState(false)

  /**
   * Kie.ai download links live ~20 minutes, so mint one on click rather than
   * on render — a link created when the video appeared would be dead by the
   * time someone came back to save it.
   */
  const handleDownload = async () => {
    setFetching(true)
    try {
      const link = await fetchDownloadUrl(url)
      window.open(link, '_blank', 'noopener,noreferrer')
    } catch (error) {
      toast.error(errorMessage(error, 'Não consegui gerar o link de download.'))
    } finally {
      setFetching(false)
    }
  }

  return (
    <div className="mb-4 space-y-3">
      <video
        src={url}
        controls
        playsInline
        className="w-full rounded-xl border border-white/10 bg-black"
      />
      <button
        onClick={handleDownload}
        disabled={fetching}
        className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-4 py-2.5 text-xs uppercase tracking-widest text-bone-200 transition hover:border-gold-400/60 hover:text-gold-200 disabled:opacity-40"
      >
        {fetching ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <Download className="h-3.5 w-3.5" />
        )}
        Baixar o vídeo
      </button>
    </div>
  )
}

function TaskPanel({ task }: { task: TaskStatus }) {
  const pct = Math.max(0, Math.min(100, Math.round(task.progress)))

  return (
    <section className="mt-8 rounded-2xl border border-white/10 bg-white/[0.02] p-7">
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
        <ResultVideo key={url} url={url} />
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
