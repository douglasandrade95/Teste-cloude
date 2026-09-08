"""Request/response schemas for the API integrations screen."""

from typing import List, Optional

from pydantic import BaseModel, Field


class CredentialStatus(BaseModel):
    configured: bool
    source: Optional[str] = Field(
        None, description="vault | env | local — where the key came from"
    )
    masked: Optional[str] = Field(None, description="Display-safe preview, never the key")
    updated_at: Optional[str] = None


class ModelInfo(BaseModel):
    id: str
    label: str
    note: str = ""
    free: bool = False


class ProviderInfo(BaseModel):
    id: str
    label: str
    tagline: str
    env_var: str
    key_url: str
    docs_url: str
    key_prefix: str = ""
    requires_key: bool = True
    free_tier: bool = False
    free_note: str = ""
    recommended: bool = False
    analysis_ready: bool = Field(
        False, description="Whether the creative-analysis engine can run on this provider"
    )
    tags: List[str] = []
    models: List[ModelInfo] = []
    credential: CredentialStatus


class ActiveSelection(BaseModel):
    active_provider: Optional[str] = None
    active_model: Optional[str] = None


class VaultInfo(BaseModel):
    encrypted: bool = True
    algorithm: str = "Fernet (AES-128-CBC + HMAC-SHA256)"
    location: str
    master_key_source: str = Field(..., description="env | file")
    writable: bool = True


class IntegrationsResponse(BaseModel):
    providers: List[ProviderInfo]
    active: ActiveSelection
    vault: VaultInfo


class SaveKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=1, description="Plaintext key; stored encrypted")
    verify: bool = Field(True, description="Test the key against the provider before saving")


class SaveKeyResponse(BaseModel):
    provider: str
    credential: CredentialStatus
    verified: bool
    message: str


class TestKeyRequest(BaseModel):
    api_key: Optional[str] = Field(
        None, description="Test this key without storing it. Omit to test the stored one."
    )


class TestKeyResponse(BaseModel):
    provider: str
    ok: bool
    message: str
    status_code: Optional[int] = None


class SelectModelRequest(BaseModel):
    provider: str
    model: str
