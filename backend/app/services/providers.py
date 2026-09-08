"""
Catalog of AI providers that can power AutoVideoEditor, plus credential
resolution and live connection testing.

A provider's key can come from two places, in this order of priority:

1. The encrypted vault  -> set through the Integrações screen in the UI.
2. An environment variable -> set through .env, Replit Secrets, Docker, etc.

That way the UI is the easy path, and a deployment can still inject keys the
usual way without anyone typing a secret into a browser.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import httpx

from app.services.vault import get_vault

logger = logging.getLogger(__name__)

TEST_TIMEOUT_SECONDS = 15.0


@dataclass(frozen=True)
class ModelOption:
    id: str
    label: str
    note: str = ""
    free: bool = False


@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    tagline: str
    env_var: str
    key_url: str
    docs_url: str
    models: List[ModelOption]
    free_tier: bool = False
    free_note: str = ""
    key_prefix: str = ""
    requires_key: bool = True
    base_url: str = ""
    test_path: str = ""
    auth_style: str = "bearer"  # bearer | x-api-key | query | token | none
    recommended: bool = False
    tags: List[str] = field(default_factory=list)

    @property
    def secret_name(self) -> str:
        return f"provider:{self.id}:api_key"


PROVIDERS: Tuple[Provider, ...] = (
    Provider(
        id="anthropic",
        label="Anthropic — Claude",
        tagline="Melhor leitura de intenção criativa e direção estética.",
        env_var="ANTHROPIC_API_KEY",
        key_url="https://console.anthropic.com/settings/keys",
        docs_url="https://docs.anthropic.com/en/api/getting-started",
        key_prefix="sk-ant-",
        base_url="https://api.anthropic.com",
        test_path="/v1/models",
        auth_style="x-api-key",
        recommended=True,
        tags=["direção criativa", "texto", "análise"],
        models=[
            ModelOption("claude-opus-5", "Claude Opus 5", "Mais profundo, direção autoral."),
            ModelOption("claude-sonnet-5", "Claude Sonnet 5", "Equilíbrio custo/qualidade."),
            ModelOption("claude-haiku-4-5-20251001", "Claude Haiku 4.5", "Rápido e barato."),
        ],
    ),
    Provider(
        id="google",
        label="Google — Gemini",
        tagline="Camada gratuita generosa. Bom ponto de partida sem cartão.",
        env_var="GOOGLE_API_KEY",
        key_url="https://aistudio.google.com/app/apikey",
        docs_url="https://ai.google.dev/gemini-api/docs",
        key_prefix="AIza",
        base_url="https://generativelanguage.googleapis.com",
        test_path="/v1beta/models",
        auth_style="query",
        free_tier=True,
        free_note="Gemini API tem camada gratuita no Google AI Studio (limite por minuto/dia).",
        tags=["grátis", "texto", "visão"],
        models=[
            ModelOption("gemini-2.0-flash", "Gemini 2.0 Flash", "Rápido, camada gratuita.", free=True),
            ModelOption("gemini-1.5-flash", "Gemini 1.5 Flash", "Barato e estável.", free=True),
            ModelOption("gemini-1.5-pro", "Gemini 1.5 Pro", "Mais preciso, limite menor."),
        ],
    ),
    Provider(
        id="groq",
        label="Groq",
        tagline="Modelos abertos com inferência muito rápida e camada gratuita.",
        env_var="GROQ_API_KEY",
        key_url="https://console.groq.com/keys",
        docs_url="https://console.groq.com/docs/quickstart",
        key_prefix="gsk_",
        base_url="https://api.groq.com/openai/v1",
        test_path="/models",
        auth_style="bearer",
        free_tier=True,
        free_note="Camada gratuita com limites de requisições por minuto.",
        tags=["grátis", "rápido"],
        models=[
            ModelOption("llama-3.3-70b-versatile", "Llama 3.3 70B", "Bom generalista.", free=True),
            ModelOption("llama-3.1-8b-instant", "Llama 3.1 8B", "Ultra rápido.", free=True),
        ],
    ),
    Provider(
        id="openrouter",
        label="OpenRouter",
        tagline="Uma chave, dezenas de modelos — incluindo modelos :free.",
        env_var="OPENROUTER_API_KEY",
        key_url="https://openrouter.ai/keys",
        docs_url="https://openrouter.ai/docs/quickstart",
        key_prefix="sk-or-",
        base_url="https://openrouter.ai/api/v1",
        test_path="/auth/key",
        auth_style="bearer",
        free_tier=True,
        free_note="Modelos com sufixo ':free' não consomem créditos.",
        tags=["grátis", "multi-modelo"],
        models=[
            ModelOption(
                "meta-llama/llama-3.3-70b-instruct:free",
                "Llama 3.3 70B (free)",
                "Sem custo por token.",
                free=True,
            ),
            ModelOption("deepseek/deepseek-chat", "DeepSeek Chat", "Muito barato."),
            ModelOption("anthropic/claude-sonnet-4.5", "Claude via OpenRouter", "Cobrança via créditos."),
        ],
    ),
    Provider(
        id="openai",
        label="OpenAI",
        tagline="Whisper para legendas automáticas e GPT para texto.",
        env_var="OPENAI_API_KEY",
        key_url="https://platform.openai.com/api-keys",
        docs_url="https://platform.openai.com/docs/quickstart",
        key_prefix="sk-",
        base_url="https://api.openai.com/v1",
        test_path="/models",
        auth_style="bearer",
        tags=["legendas", "texto"],
        models=[
            ModelOption("gpt-4o-mini", "GPT-4o mini", "Barato para tarefas simples."),
            ModelOption("gpt-4o", "GPT-4o", "Multimodal."),
            ModelOption("whisper-1", "Whisper", "Transcrição / legendas."),
        ],
    ),
    Provider(
        id="deepseek",
        label="DeepSeek",
        tagline="Custo por token muito baixo para volume alto.",
        env_var="DEEPSEEK_API_KEY",
        key_url="https://platform.deepseek.com/api_keys",
        docs_url="https://api-docs.deepseek.com/",
        key_prefix="sk-",
        base_url="https://api.deepseek.com",
        test_path="/models",
        auth_style="bearer",
        tags=["barato"],
        models=[
            ModelOption("deepseek-chat", "DeepSeek Chat", "Generalista."),
            ModelOption("deepseek-reasoner", "DeepSeek Reasoner", "Raciocínio mais longo."),
        ],
    ),
    Provider(
        id="replicate",
        label="Replicate",
        tagline="Modelos de vídeo/imagem prontos para inferência.",
        env_var="REPLICATE_API_TOKEN",
        key_url="https://replicate.com/account/api-tokens",
        docs_url="https://replicate.com/docs",
        key_prefix="r8_",
        base_url="https://api.replicate.com/v1",
        test_path="/account",
        auth_style="token",
        tags=["vídeo", "imagem"],
        models=[
            ModelOption("black-forest-labs/flux-schnell", "FLUX schnell", "Imagem rápida."),
            ModelOption("stability-ai/stable-video-diffusion", "Stable Video", "Vídeo curto."),
        ],
    ),
    Provider(
        id="ollama",
        label="Ollama (local)",
        tagline="Roda no seu próprio computador. Zero custo, zero chave.",
        env_var="OLLAMA_BASE_URL",
        key_url="https://ollama.com/download",
        docs_url="https://github.com/ollama/ollama/blob/main/docs/api.md",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        test_path="/api/tags",
        auth_style="none",
        requires_key=False,
        free_tier=True,
        free_note="100% gratuito: os modelos rodam na sua máquina, nada sai dela.",
        tags=["grátis", "local", "privado"],
        models=[
            ModelOption("llama3.2", "Llama 3.2", "Leve, roda em notebook.", free=True),
            ModelOption("qwen2.5", "Qwen 2.5", "Bom em português.", free=True),
        ],
    ),
)

PROVIDERS_BY_ID: Dict[str, Provider] = {p.id: p for p in PROVIDERS}


def get_provider(provider_id: str) -> Optional[Provider]:
    return PROVIDERS_BY_ID.get(provider_id)


# ----------------------------------------------------------------------
# Credential resolution
# ----------------------------------------------------------------------
def resolve_key(provider_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (plaintext_key, source) for a provider.

    source is "vault", "env" or None. Callers must never echo the key back
    to a client — use `describe_credential` for anything user-facing.
    """
    provider = get_provider(provider_id)
    if provider is None:
        return None, None

    vault_key = get_vault().get_secret(provider.secret_name)
    if vault_key:
        return vault_key, "vault"

    env_key = (os.getenv(provider.env_var) or "").strip()
    if env_key and not env_key.lower().startswith("your_"):
        return env_key, "env"

    return None, None


def describe_credential(provider_id: str) -> Dict:
    """Non-sensitive status for one provider, safe to send to the browser."""
    provider = get_provider(provider_id)
    if provider is None:
        return {"configured": False, "source": None, "masked": None, "updated_at": None}

    stored = get_vault().describe(provider.secret_name)
    if stored:
        return {
            "configured": True,
            "source": "vault",
            "masked": stored["masked"],
            "updated_at": stored["updated_at"],
        }

    env_key, source = resolve_key(provider_id)
    if env_key:
        return {
            "configured": True,
            "source": source,
            "masked": _mask_raw(env_key),
            "updated_at": None,
        }

    if not provider.requires_key:
        return {"configured": True, "source": "local", "masked": None, "updated_at": None}

    return {"configured": False, "source": None, "masked": None, "updated_at": None}


def _mask_raw(value: str) -> str:
    from app.services.vault import SecretVault

    return SecretVault.mask(value[-4:], len(value))


def validate_key_shape(provider: Provider, key: str) -> Optional[str]:
    """Cheap sanity check before we bother the provider's API. None = OK."""
    key = (key or "").strip()
    if not key:
        return "A chave não pode ficar vazia."
    if len(key) < 12:
        return "Essa chave parece curta demais — confira se copiou inteira."
    if any(ch.isspace() for ch in key):
        return "A chave contém espaços ou quebras de linha. Cole apenas a chave."
    if provider.key_prefix and not key.startswith(provider.key_prefix):
        return (
            f"Chaves da {provider.label} normalmente começam com "
            f"'{provider.key_prefix}'. Confira se pegou a chave certa."
        )
    return None


# ----------------------------------------------------------------------
# Live connection test
# ----------------------------------------------------------------------
def _build_test_request(provider: Provider, key: Optional[str]) -> Tuple[str, Dict[str, str]]:
    url = f"{provider.base_url.rstrip('/')}{provider.test_path}"
    headers: Dict[str, str] = {"Accept": "application/json"}

    if provider.auth_style == "bearer":
        headers["Authorization"] = f"Bearer {key}"
    elif provider.auth_style == "token":
        headers["Authorization"] = f"Token {key}"
    elif provider.auth_style == "x-api-key":
        headers["x-api-key"] = key or ""
        headers["anthropic-version"] = "2023-06-01"
    elif provider.auth_style == "query":
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}key={key}"

    return url, headers


async def test_provider_connection(provider: Provider, key: Optional[str]) -> Dict:
    """
    Hit a cheap read-only endpoint to confirm the credential actually works.
    Returns {"ok": bool, "message": str, "status_code": int | None}.
    """
    if provider.requires_key and not key:
        return {
            "ok": False,
            "message": "Nenhuma chave configurada para este provedor.",
            "status_code": None,
        }

    url, headers = _build_test_request(provider, key)

    try:
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=headers)
    except httpx.TimeoutException:
        return {
            "ok": False,
            "message": "Tempo esgotado ao falar com o provedor. Tente de novo.",
            "status_code": None,
        }
    except httpx.HTTPError as exc:
        logger.warning("Connection test failed for %s: %s", provider.id, exc)
        message = (
            "Não consegui alcançar o servidor local do Ollama. Ele está rodando?"
            if provider.id == "ollama"
            else "Não consegui alcançar o provedor. Verifique sua conexão."
        )
        return {"ok": False, "message": message, "status_code": None}

    if response.status_code < 300:
        return {
            "ok": True,
            "message": "Conexão confirmada. A chave está válida.",
            "status_code": response.status_code,
        }

    # Google answers an invalid key with 400 API_KEY_INVALID rather than 401.
    invalid_key_codes = (400, 401, 403) if provider.auth_style == "query" else (401, 403)
    if response.status_code in invalid_key_codes:
        return {
            "ok": False,
            "message": "O provedor recusou a chave (não autorizada). Gere uma nova.",
            "status_code": response.status_code,
        }

    if response.status_code == 429:
        return {
            "ok": True,
            "message": "Chave válida, mas você atingiu o limite de requisições agora.",
            "status_code": response.status_code,
        }

    return {
        "ok": False,
        "message": f"O provedor respondeu com HTTP {response.status_code}.",
        "status_code": response.status_code,
    }


def serialize_provider(provider: Provider) -> Dict:
    """Full catalog entry + credential status, safe for the browser."""
    return {
        "id": provider.id,
        "label": provider.label,
        "tagline": provider.tagline,
        "env_var": provider.env_var,
        "key_url": provider.key_url,
        "docs_url": provider.docs_url,
        "key_prefix": provider.key_prefix,
        "requires_key": provider.requires_key,
        "free_tier": provider.free_tier,
        "free_note": provider.free_note,
        "recommended": provider.recommended,
        "tags": list(provider.tags),
        "models": [
            {"id": m.id, "label": m.label, "note": m.note, "free": m.free}
            for m in provider.models
        ],
        "credential": describe_credential(provider.id),
    }
