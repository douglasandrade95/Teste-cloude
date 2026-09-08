import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import {
  CheckCircle2,
  ExternalLink,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  Lock,
  Plug,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Trash2,
  XCircle,
} from 'lucide-react'

import {
  ActiveSelection,
  IntegrationsResponse,
  ProviderInfo,
  VaultInfo,
  deleteProviderKey,
  errorMessage,
  fetchIntegrations,
  getAdminToken,
  saveProviderKey,
  setActiveModel,
  setAdminToken,
  testProviderKey,
} from '../services/api'

type Busy = 'idle' | 'testing' | 'saving' | 'deleting' | 'activating'

function formatDate(iso: string | null): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ''
  }
}

function sourceLabel(source: string | null): string {
  switch (source) {
    case 'vault':
      return 'Cofre criptografado'
    case 'env':
      return 'Variável de ambiente'
    case 'local':
      return 'Local, sem chave'
    default:
      return 'Não configurado'
  }
}

export function Integrations() {
  const [data, setData] = useState<IntegrationsResponse | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [keyInput, setKeyInput] = useState('')
  const [revealKey, setRevealKey] = useState(false)
  const [busy, setBusy] = useState<Busy>('idle')
  const [loading, setLoading] = useState(true)
  const [locked, setLocked] = useState(false)
  const [tokenInput, setTokenInput] = useState(getAdminToken())
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const response = await fetchIntegrations()
      setData(response)
      setLocked(false)
      setSelectedId((current) => {
        if (current && response.providers.some((p) => p.id === current)) return current
        return response.active.active_provider ?? response.providers[0]?.id ?? null
      })
    } catch (error) {
      if (axios.isAxiosError(error) && [401, 403].includes(error.response?.status ?? 0)) {
        setLocked(true)
      } else {
        toast.error(errorMessage(error, 'Não consegui carregar as integrações.'))
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const provider = useMemo<ProviderInfo | null>(
    () => data?.providers.find((p) => p.id === selectedId) ?? null,
    [data, selectedId]
  )

  const active: ActiveSelection = data?.active ?? { active_provider: null, active_model: null }

  const selectProvider = (id: string) => {
    setSelectedId(id)
    setKeyInput('')
    setRevealKey(false)
    setTestResult(null)
  }

  const handleTest = async () => {
    if (!provider) return
    setBusy('testing')
    setTestResult(null)
    try {
      const result = await testProviderKey(provider.id, keyInput.trim() || undefined)
      setTestResult({ ok: result.ok, message: result.message })
      if (result.ok) toast.success(result.message)
      else toast.error(result.message)
    } catch (error) {
      toast.error(errorMessage(error, 'Falha ao testar a conexão.'))
    } finally {
      setBusy('idle')
    }
  }

  const handleSave = async () => {
    if (!provider) return
    const apiKey = keyInput.trim()
    if (!apiKey) {
      toast.error('Cole a chave antes de salvar.')
      return
    }

    setBusy('saving')
    try {
      const result = await saveProviderKey(provider.id, apiKey, true)
      toast.success(result.message)
      setKeyInput('')
      setRevealKey(false)
      setTestResult({ ok: true, message: result.message })
      await load()
    } catch (error) {
      toast.error(errorMessage(error, 'Não consegui salvar a chave.'))
    } finally {
      setBusy('idle')
    }
  }

  const handleDelete = async () => {
    if (!provider) return
    setBusy('deleting')
    try {
      await deleteProviderKey(provider.id)
      toast.success('Chave removida do cofre.')
      setTestResult(null)
      await load()
    } catch (error) {
      toast.error(errorMessage(error, 'Não consegui remover a chave.'))
    } finally {
      setBusy('idle')
    }
  }

  const handleActivate = async (modelId: string) => {
    if (!provider) return
    setBusy('activating')
    try {
      await setActiveModel(provider.id, modelId)
      toast.success('Modelo ativado para as próximas análises.')
      await load()
    } catch (error) {
      toast.error(errorMessage(error, 'Não consegui ativar esse modelo.'))
    } finally {
      setBusy('idle')
    }
  }

  const handleUnlock = () => {
    setAdminToken(tokenInput.trim())
    void load()
  }

  if (locked) {
    return <LockedPanel token={tokenInput} onChange={setTokenInput} onSubmit={handleUnlock} />
  }

  return (
    <div className="min-h-screen bg-ink-950 text-bone-100">
      <div className="mx-auto max-w-6xl px-5 py-14">
        <header className="mb-12 border-b border-white/10 pb-10">
          <p className="mb-3 text-[11px] uppercase tracking-luxe text-gold-400">
            Configuração
          </p>
          <h1 className="font-display text-5xl font-light tracking-tight text-bone-50">
            Integrações de API
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-bone-300">
            Escolha o provedor e o modelo que vão dirigir as análises. A chave é
            guardada criptografada no seu cofre local — ela nunca aparece no
            código, nunca vai para o Git e nunca volta pela tela.
          </p>
        </header>

        {data?.vault && <VaultStrip vault={data.vault} />}

        {loading && !data ? (
          <div className="flex items-center gap-3 py-24 text-bone-300">
            <Loader2 className="h-5 w-5 animate-spin text-gold-400" />
            Carregando provedores…
          </div>
        ) : (
          <div className="mt-10 grid gap-8 lg:grid-cols-[340px_1fr]">
            {/* Provider list */}
            <nav className="space-y-2" aria-label="Provedores de API">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-[11px] uppercase tracking-luxe text-bone-300">
                  Provedores
                </h2>
                <button
                  onClick={() => void load()}
                  className="flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-bone-300 transition hover:text-gold-400"
                >
                  <RefreshCw className="h-3 w-3" />
                  Atualizar
                </button>
              </div>

              {data?.providers.map((item) => (
                <ProviderCard
                  key={item.id}
                  provider={item}
                  selected={item.id === selectedId}
                  isActive={active.active_provider === item.id}
                  onSelect={() => selectProvider(item.id)}
                />
              ))}
            </nav>

            {/* Detail panel */}
            <section>
              {provider ? (
                <ProviderDetail
                  provider={provider}
                  active={active}
                  keyInput={keyInput}
                  onKeyInput={setKeyInput}
                  revealKey={revealKey}
                  onToggleReveal={() => setRevealKey((v) => !v)}
                  busy={busy}
                  testResult={testResult}
                  onTest={handleTest}
                  onSave={handleSave}
                  onDelete={handleDelete}
                  onActivate={handleActivate}
                />
              ) : (
                <p className="text-bone-300">Selecione um provedor à esquerda.</p>
              )}
            </section>
          </div>
        )}

        <SecurityNotes />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------

function VaultStrip({ vault }: { vault: VaultInfo }) {
  return (
    <div className="flex flex-wrap items-center gap-x-8 gap-y-3 rounded-xl border border-gold-400/20 bg-gold-400/[0.04] px-6 py-4">
      <span className="flex items-center gap-2 text-sm text-gold-200">
        <ShieldCheck className="h-4 w-4" />
        Cofre criptografado
      </span>
      <span className="text-xs text-bone-300">{vault.algorithm}</span>
      <span className="text-xs text-bone-300">
        Arquivo: <code className="text-bone-200">{vault.location}</code>
      </span>
      <span className="text-xs text-bone-300">
        Chave mestra:{' '}
        <strong className="font-medium text-bone-100">
          {vault.master_key_source === 'env'
            ? 'variável de ambiente'
            : 'arquivo local (0600)'}
        </strong>
      </span>
      {!vault.writable && (
        <span className="flex items-center gap-1.5 text-xs text-red-300">
          <XCircle className="h-3.5 w-3.5" />
          Cofre indisponível
        </span>
      )}
    </div>
  )
}

function ProviderCard({
  provider,
  selected,
  isActive,
  onSelect,
}: {
  provider: ProviderInfo
  selected: boolean
  isActive: boolean
  onSelect: () => void
}) {
  const configured = provider.credential.configured

  return (
    <button
      onClick={onSelect}
      aria-current={selected}
      className={`w-full rounded-xl border px-5 py-4 text-left transition ${
        selected
          ? 'border-gold-400/60 bg-gold-400/[0.07]'
          : 'border-white/10 bg-white/[0.02] hover:border-white/25'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium text-bone-50">{provider.label}</p>
          <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-bone-300">
            {provider.tagline}
          </p>
        </div>
        <span
          aria-hidden
          className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
            configured ? 'bg-emerald-400' : 'bg-white/25'
          }`}
        />
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {provider.free_tier && <Badge tone="gold">Grátis</Badge>}
        {provider.recommended && <Badge tone="neutral">Recomendado</Badge>}
        {isActive && <Badge tone="active">Em uso</Badge>}
        {configured && !isActive && (
          <Badge tone="ok">{sourceLabel(provider.credential.source)}</Badge>
        )}
      </div>
    </button>
  )
}

type BadgeTone = 'neutral' | 'gold' | 'ok' | 'active'

function Badge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode
  tone?: BadgeTone
}) {
  const tones: Record<BadgeTone, string> = {
    neutral: 'border-white/15 text-bone-300',
    gold: 'border-gold-400/40 text-gold-300',
    ok: 'border-emerald-400/30 text-emerald-300/90',
    active: 'border-gold-400 bg-gold-400/10 text-gold-200',
  }
  return (
    <span
      className={`rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-widest ${tones[tone]}`}
    >
      {children}
    </span>
  )
}

function ProviderDetail({
  provider,
  active,
  keyInput,
  onKeyInput,
  revealKey,
  onToggleReveal,
  busy,
  testResult,
  onTest,
  onSave,
  onDelete,
  onActivate,
}: {
  provider: ProviderInfo
  active: ActiveSelection
  keyInput: string
  onKeyInput: (value: string) => void
  revealKey: boolean
  onToggleReveal: () => void
  busy: Busy
  testResult: { ok: boolean; message: string } | null
  onTest: () => void
  onSave: () => void
  onDelete: () => void
  onActivate: (modelId: string) => void
}) {
  const credential = provider.credential
  const working = busy !== 'idle'

  return (
    <div className="space-y-8 rounded-2xl border border-white/10 bg-white/[0.02] p-8">
      {/* Heading */}
      <div>
        <h2 className="font-display text-3xl font-light text-bone-50">{provider.label}</h2>
        <p className="mt-2 text-sm leading-relaxed text-bone-300">{provider.tagline}</p>
        {provider.free_tier && provider.free_note && (
          <p className="mt-3 rounded-lg border border-gold-400/25 bg-gold-400/[0.05] px-4 py-2.5 text-xs leading-relaxed text-gold-200">
            {provider.free_note}
          </p>
        )}
      </div>

      {/* Current status */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-xl border border-white/10 bg-black/30 px-5 py-4">
        {credential.configured ? (
          <>
            <span className="flex items-center gap-2 text-sm text-emerald-300">
              <CheckCircle2 className="h-4 w-4" />
              Configurado
            </span>
            {credential.masked && (
              <code className="font-mono text-sm text-bone-200">{credential.masked}</code>
            )}
            <span className="text-xs text-bone-300">
              via {sourceLabel(credential.source)}
            </span>
            {credential.updated_at && (
              <span className="text-xs text-bone-300">
                Atualizada em {formatDate(credential.updated_at)}
              </span>
            )}
          </>
        ) : (
          <span className="flex items-center gap-2 text-sm text-bone-300">
            <KeyRound className="h-4 w-4" />
            Nenhuma chave cadastrada ainda
          </span>
        )}
      </div>

      {/* Key form */}
      {provider.requires_key ? (
        <div>
          <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
            <label
              htmlFor="api-key-input"
              className="text-[11px] uppercase tracking-luxe text-bone-300"
            >
              {credential.source === 'vault' ? 'Substituir a chave' : 'Colar a chave'}
            </label>
            <a
              href={provider.key_url}
              target="_blank"
              rel="noreferrer noopener"
              className="flex items-center gap-1.5 text-xs text-gold-400 transition hover:text-gold-300"
            >
              Onde pegar a chave
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          <div className="relative">
            <input
              id="api-key-input"
              type={revealKey ? 'text' : 'password'}
              value={keyInput}
              onChange={(e) => onKeyInput(e.target.value)}
              autoComplete="off"
              spellCheck={false}
              placeholder={provider.key_prefix ? `${provider.key_prefix}…` : 'sua chave'}
              className="w-full rounded-xl border border-white/15 bg-black/40 px-5 py-3.5 pr-12 font-mono text-sm text-bone-50 outline-none transition placeholder:text-white/25 focus:border-gold-400/70"
            />
            <button
              type="button"
              onClick={onToggleReveal}
              aria-label={revealKey ? 'Ocultar chave' : 'Mostrar chave'}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-bone-300 transition hover:text-gold-400"
            >
              {revealKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          <p className="mt-2.5 text-xs leading-relaxed text-bone-300">
            Ao salvar, a chave é testada no provedor e só então gravada
            criptografada. Depois disso nem esta tela consegue lê-la de volta —
            só substituir ou apagar.
          </p>

          {testResult && (
            <p
              className={`mt-4 flex items-start gap-2 rounded-lg border px-4 py-3 text-sm ${
                testResult.ok
                  ? 'border-emerald-400/30 bg-emerald-400/[0.06] text-emerald-200'
                  : 'border-red-400/30 bg-red-400/[0.06] text-red-200'
              }`}
            >
              {testResult.ok ? (
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              ) : (
                <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
              )}
              {testResult.message}
            </p>
          )}

          <div className="mt-5 flex flex-wrap gap-3">
            <button
              onClick={onSave}
              disabled={working || !keyInput.trim()}
              className="flex items-center gap-2 rounded-xl bg-gold-400 px-6 py-3 text-sm font-medium text-ink-950 transition hover:bg-gold-300 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-white/40"
            >
              {busy === 'saving' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Lock className="h-4 w-4" />
              )}
              Salvar com segurança
            </button>

            <button
              onClick={onTest}
              disabled={working || (!keyInput.trim() && !credential.configured)}
              className="flex items-center gap-2 rounded-xl border border-white/20 px-6 py-3 text-sm text-bone-100 transition hover:border-gold-400/60 hover:text-gold-200 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {busy === 'testing' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plug className="h-4 w-4" />
              )}
              Testar conexão
            </button>

            {credential.source === 'vault' && (
              <button
                onClick={onDelete}
                disabled={working}
                className="flex items-center gap-2 rounded-xl border border-red-400/30 px-6 py-3 text-sm text-red-200 transition hover:bg-red-400/10 disabled:opacity-40"
              >
                {busy === 'deleting' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Remover
              </button>
            )}
          </div>

          <p className="mt-5 text-xs leading-relaxed text-bone-300">
            Prefere não usar esta tela? Dá no mesmo definir a variável de
            ambiente{' '}
            <code className="rounded bg-white/10 px-1.5 py-0.5 text-bone-100">
              {provider.env_var}
            </code>{' '}
            no <code className="text-bone-100">.env</code> ou nos secrets da sua
            hospedagem. O cofre tem prioridade sobre ela.
          </p>
        </div>
      ) : (
        <p className="rounded-xl border border-white/10 bg-black/30 px-5 py-4 text-sm leading-relaxed text-bone-300">
          {provider.label} roda na sua própria máquina e não pede chave nenhuma.
          Instale pelo site oficial, deixe o serviço rodando e use “Testar
          conexão” para confirmar.
        </p>
      )}

      {/* Model picker */}
      <div>
        <h3 className="mb-4 text-[11px] uppercase tracking-luxe text-bone-300">
          Modelo
        </h3>
        {!provider.analysis_ready && (
          <p className="mb-4 rounded-lg border border-white/10 bg-black/30 px-4 py-3 text-xs leading-relaxed text-bone-300">
            A chave fica guardada e testada aqui, mas a análise criativa ainda
            roda só em modelos Claude. Estes modelos entram quando o motor de
            análise passar a falar com outros provedores.
          </p>
        )}
        <div className="space-y-2">
          {provider.models.map((model) => {
            const isActive =
              active.active_provider === provider.id && active.active_model === model.id
            return (
              <div
                key={model.id}
                className={`flex flex-wrap items-center justify-between gap-4 rounded-xl border px-5 py-4 transition ${
                  isActive
                    ? 'border-gold-400/60 bg-gold-400/[0.07]'
                    : 'border-white/10 bg-white/[0.02]'
                }`}
              >
                <div className="min-w-0">
                  <p className="flex items-center gap-2 font-medium text-bone-50">
                    {model.label}
                    {model.free && <Badge tone="gold">Grátis</Badge>}
                  </p>
                  <p className="mt-1 font-mono text-[11px] text-bone-300">{model.id}</p>
                  {model.note && (
                    <p className="mt-1 text-xs text-bone-300">{model.note}</p>
                  )}
                </div>

                {isActive ? (
                  <span className="flex items-center gap-2 text-sm text-gold-300">
                    <Sparkles className="h-4 w-4" />
                    Em uso
                  </span>
                ) : (
                  <button
                    onClick={() => onActivate(model.id)}
                    disabled={
                      working ||
                      !provider.credential.configured ||
                      !provider.analysis_ready
                    }
                    title={
                      !provider.credential.configured
                        ? 'Configure a chave deste provedor primeiro'
                        : !provider.analysis_ready
                          ? 'A análise criativa ainda roda só em modelos Claude'
                          : undefined
                    }
                    className="rounded-lg border border-white/20 px-4 py-2 text-xs uppercase tracking-widest text-bone-200 transition hover:border-gold-400/60 hover:text-gold-200 disabled:cursor-not-allowed disabled:opacity-35"
                  >
                    Ativar
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function LockedPanel({
  token,
  onChange,
  onSubmit,
}: {
  token: string
  onChange: (value: string) => void
  onSubmit: () => void
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-950 px-5">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-white/[0.02] p-8">
        <Lock className="mb-5 h-6 w-6 text-gold-400" />
        <h1 className="font-display text-3xl font-light text-bone-50">
          Acesso protegido
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-bone-300">
          Este backend não está rodando na sua máquina, então as credenciais só
          podem ser alteradas com o token de administração
          (<code className="text-bone-100">AVE_ADMIN_TOKEN</code>).
        </p>

        <input
          type="password"
          value={token}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onSubmit()}
          placeholder="Token de administração"
          autoComplete="off"
          className="mt-6 w-full rounded-xl border border-white/15 bg-black/40 px-5 py-3.5 font-mono text-sm text-bone-50 outline-none transition placeholder:text-white/25 focus:border-gold-400/70"
        />

        <button
          onClick={onSubmit}
          className="mt-4 w-full rounded-xl bg-gold-400 px-6 py-3 text-sm font-medium text-ink-950 transition hover:bg-gold-300"
        >
          Entrar
        </button>

        <p className="mt-4 text-xs leading-relaxed text-bone-300">
          O token fica só nesta aba do navegador e some quando você fecha.
        </p>
      </div>
    </div>
  )
}

function SecurityNotes() {
  const items = [
    {
      title: 'Criptografada em repouso',
      body: 'A chave é gravada com Fernet (AES-128-CBC + HMAC-SHA256) em um arquivo fora do repositório, com permissão só para o seu usuário.',
    },
    {
      title: 'Nunca volta pela tela',
      body: 'Nenhum endpoint devolve a chave em texto. A interface só recebe os 4 últimos caracteres, o suficiente para você reconhecer qual é.',
    },
    {
      title: 'Fora do Git',
      body: 'O cofre mora em ~/.autovideoeditor e o .gitignore bloqueia master.key, secrets.enc e .env. Não tem como subir sem querer.',
    },
    {
      title: 'Fechada por padrão',
      body: 'Só a própria máquina altera credenciais. Para liberar acesso remoto é preciso definir AVE_ADMIN_TOKEN no servidor.',
    },
  ]

  return (
    <section className="mt-16 border-t border-white/10 pt-10">
      <h2 className="mb-6 text-[11px] uppercase tracking-luxe text-gold-400">
        Como a sua chave é protegida
      </h2>
      <div className="grid gap-6 sm:grid-cols-2">
        {items.map((item) => (
          <div key={item.title}>
            <h3 className="mb-1.5 text-sm font-medium text-bone-50">{item.title}</h3>
            <p className="text-xs leading-relaxed text-bone-300">{item.body}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
