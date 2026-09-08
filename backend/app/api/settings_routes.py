"""
Endpoints behind the "Integrações de API" screen.

Security posture:
- A stored key can be written, tested and deleted, but never read back.
  Every response carries only a masked preview.
- The whole router is guarded (see `require_settings_access`): loopback-only
  by default, or an admin token when the backend is exposed to a network.
"""

import hmac
import ipaddress
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.settings_schemas import (
    ActiveSelection,
    IntegrationsResponse,
    SaveKeyRequest,
    SaveKeyResponse,
    SelectModelRequest,
    TestKeyRequest,
    TestKeyResponse,
    VaultInfo,
)
from app.services import providers as provider_service
from app.services.preferences import load_preferences, save_preferences
from app.services.vault import MASTER_KEY_ENV, VaultError, get_vault

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

ADMIN_TOKEN_ENV = "AVE_ADMIN_TOKEN"
ALLOW_REMOTE_ENV = "AVE_SETTINGS_ALLOW_REMOTE"


def _is_loopback(host: Optional[str]) -> bool:
    if not host:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


async def require_settings_access(request: Request) -> None:
    """
    Guard the credential endpoints.

    - AVE_ADMIN_TOKEN set -> the X-Admin-Token header must match.
    - Otherwise           -> only requests coming from localhost are allowed,
                             unless AVE_SETTINGS_ALLOW_REMOTE=true.
    """
    admin_token = (os.getenv(ADMIN_TOKEN_ENV) or "").strip()
    if admin_token:
        # Constant-time comparison to avoid leaking the token through timing.
        provided = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(provided, admin_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de administração inválido ou ausente.",
            )
        return

    if os.getenv(ALLOW_REMOTE_ENV, "").lower() in ("1", "true", "yes"):
        return

    client_host = request.client.host if request.client else None
    if not _is_loopback(client_host):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "As configurações de API só podem ser alteradas a partir da "
                f"própria máquina. Para liberar acesso remoto, defina {ADMIN_TOKEN_ENV}."
            ),
        )


def _vault_info() -> VaultInfo:
    vault = get_vault()
    writable = True
    try:
        vault.list_names()
    except VaultError as exc:
        logger.error("Vault unavailable: %s", exc)
        writable = False

    return VaultInfo(
        location=str(vault.secrets_path),
        master_key_source=vault.master_key_source,
        writable=writable,
    )


def _require_provider(provider_id: str):
    provider = provider_service.get_provider(provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail=f"Provedor '{provider_id}' não existe.")
    return provider


@router.get("/integrations", response_model=IntegrationsResponse)
async def list_integrations(_: None = Depends(require_settings_access)):
    """Catalog of providers, their models, and whether a key is configured."""
    prefs = load_preferences()
    return IntegrationsResponse(
        providers=[provider_service.serialize_provider(p) for p in provider_service.PROVIDERS],
        active=ActiveSelection(**prefs),
        vault=_vault_info(),
    )


@router.put("/providers/{provider_id}/key", response_model=SaveKeyResponse)
async def save_provider_key(
    provider_id: str,
    payload: SaveKeyRequest,
    _: None = Depends(require_settings_access),
):
    """Store an API key, encrypted. The key is never returned by any endpoint."""
    provider = _require_provider(provider_id)

    if not provider.requires_key:
        raise HTTPException(
            status_code=400,
            detail=f"{provider.label} roda localmente e não usa chave de API.",
        )

    api_key = payload.api_key.strip()
    shape_error = provider_service.validate_key_shape(provider, api_key)
    if shape_error:
        raise HTTPException(status_code=422, detail=shape_error)

    verified = False
    message = "Chave salva com segurança."

    if payload.verify:
        result = await provider_service.test_provider_connection(provider, api_key)
        verified = bool(result["ok"])
        if not verified:
            # Don't persist a key the provider already rejected.
            raise HTTPException(status_code=400, detail=result["message"])
        message = f"Chave salva e verificada. {result['message']}"

    try:
        get_vault().set_secret(provider.secret_name, api_key, provider=provider.id)
    except (VaultError, ValueError) as exc:
        logger.error("Failed to store key for %s: %s", provider.id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    logger.info("Stored API key for provider '%s' (verified=%s)", provider.id, verified)

    return SaveKeyResponse(
        provider=provider.id,
        credential=provider_service.describe_credential(provider.id),
        verified=verified,
        message=message,
    )


@router.delete("/providers/{provider_id}/key", status_code=status.HTTP_200_OK)
async def delete_provider_key(provider_id: str, _: None = Depends(require_settings_access)):
    """Remove a stored key. A key coming from an env var is untouched."""
    provider = _require_provider(provider_id)

    removed = get_vault().delete_secret(provider.secret_name)
    credential = provider_service.describe_credential(provider.id)

    detail = "Chave removida do cofre."
    if not removed:
        detail = "Nenhuma chave estava guardada no cofre para este provedor."
    elif credential["source"] == "env":
        detail = (
            "Chave removida do cofre. Ainda existe uma chave vinda da variável "
            f"de ambiente {provider.env_var}."
        )

    return {"provider": provider.id, "removed": removed, "detail": detail, "credential": credential}


@router.post("/providers/{provider_id}/test", response_model=TestKeyResponse)
async def test_provider_key(
    provider_id: str,
    payload: Optional[TestKeyRequest] = None,
    _: None = Depends(require_settings_access),
):
    """
    Test a connection. With `api_key` in the body it tests that candidate key
    without storing it; otherwise it tests whatever is already configured.
    """
    provider = _require_provider(provider_id)

    candidate = (payload.api_key or "").strip() if payload and payload.api_key else None
    if candidate:
        shape_error = provider_service.validate_key_shape(provider, candidate)
        if shape_error:
            return TestKeyResponse(provider=provider.id, ok=False, message=shape_error)
        key = candidate
    else:
        key, _source = provider_service.resolve_key(provider.id)

    result = await provider_service.test_provider_connection(provider, key)
    return TestKeyResponse(
        provider=provider.id,
        ok=result["ok"],
        message=result["message"],
        status_code=result["status_code"],
    )


@router.get("/active-model", response_model=ActiveSelection)
async def get_active_model(_: None = Depends(require_settings_access)):
    return ActiveSelection(**load_preferences())


@router.put("/active-model", response_model=ActiveSelection)
async def set_active_model(
    payload: SelectModelRequest,
    _: None = Depends(require_settings_access),
):
    """Pick which provider/model the editor should use."""
    provider = _require_provider(payload.provider)

    known_models = {m.id for m in provider.models}
    if payload.model not in known_models:
        raise HTTPException(
            status_code=422,
            detail=f"Modelo '{payload.model}' não pertence a {provider.label}.",
        )

    credential = provider_service.describe_credential(provider.id)
    if not credential["configured"]:
        raise HTTPException(
            status_code=400,
            detail=f"Configure a chave de {provider.label} antes de ativar este modelo.",
        )

    if not provider.analysis_ready:
        # Refuse here rather than letting the upload fail later with a
        # confusing error: the analysis engine only speaks the Anthropic API.
        raise HTTPException(
            status_code=400,
            detail=(
                f"A chave de {provider.label} fica guardada e testada, mas a análise "
                "criativa ainda roda só em modelos Claude. Ative um deles para editar."
            ),
        )

    prefs = save_preferences(active_provider=provider.id, active_model=payload.model)
    logger.info("Active model set to %s / %s", prefs["active_provider"], prefs["active_model"])
    return ActiveSelection(**prefs)


@router.get("/vault", response_model=VaultInfo)
async def get_vault_info(_: None = Depends(require_settings_access)):
    """Where and how credentials are stored — useful for the UI's security panel."""
    return _vault_info()


@router.get("/vault/master-key-help")
async def master_key_help(_: None = Depends(require_settings_access)):
    """Instructions for pinning the encryption key through the environment."""
    vault = get_vault()
    return {
        "env_var": MASTER_KEY_ENV,
        "current_source": vault.master_key_source,
        "generate_command": (
            "python -c \"from cryptography.fernet import Fernet; "
            'print(Fernet.generate_key().decode())"'
        ),
        "explanation": (
            "Sem essa variável, a chave de criptografia é gerada e guardada em "
            f"{vault.master_key_path} (permissão 0600). Em servidores, defina "
            f"{MASTER_KEY_ENV} nos secrets da plataforma: aí o cofre não pode ser "
            "aberto por ninguém que só tenha o arquivo."
        ),
    }
