"""Request/response schemas for AI video generation."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FieldSpec(BaseModel):
    """One parameter, as published by the provider. Drives the rendered form."""

    name: str
    type: str = "string"
    item_type: Optional[str] = None
    enum: Optional[List[str]] = None
    default: Optional[Any] = None
    max_length: Optional[int] = None
    max_items: Optional[int] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    description: str = ""
    required: bool = False


class ModelSpec(BaseModel):
    id: str
    label: str
    category: str
    category_label: str
    docs_url: str = ""
    fields: List[FieldSpec] = []
    constraints: Dict[str, Any] = {}


class GenerationCatalog(BaseModel):
    configured: bool
    models: List[ModelSpec]
    categories: List[Dict[str, str]] = []


class GenerateVideoRequest(BaseModel):
    model: str = Field(..., description="Kie.ai model id from the catalog")
    values: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameter values, validated against the model's schema",
    )
    callback_url: Optional[str] = Field(
        None, description="Optional webhook; without it, poll the status endpoint"
    )


class GenerateVideoResponse(BaseModel):
    task_id: str
    model: str
    state: str = "waiting"
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    model: str = ""
    state: str = Field(..., description="waiting | queuing | generating | success | fail")
    finished: bool
    succeeded: bool
    progress: float = 0.0
    result_urls: List[str] = []
    credits_consumed: Optional[float] = None
    cost_time_ms: Optional[int] = None
    fail_message: str = ""


class DownloadUrlRequest(BaseModel):
    url: str = Field(..., description="A result URL produced by Kie.ai")


class DownloadUrlResponse(BaseModel):
    download_url: str
    expires_in_minutes: int = Field(..., description="The link stops working after this long")


class CreditsResponse(BaseModel):
    credits: float
    provider: str = "kie"
