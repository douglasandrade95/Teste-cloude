"""
AI video generation through Kie.ai.

Flow: POST /generate/video queues a job and returns immediately with a task id;
GET /generate/task/{task_id} reports progress and, once done, the result URLs.
Generation takes minutes, so nothing here blocks on the provider.
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from app.models.generation_schemas import (
    CreditsResponse,
    DownloadUrlRequest,
    DownloadUrlResponse,
    FieldSpec,
    GenerateVideoRequest,
    GenerateVideoResponse,
    GenerationCatalog,
    ModelSpec,
    TaskStatusResponse,
)
from app.services.kie_client import (
    DOWNLOAD_LINK_TTL_MINUTES,
    KieAuthError,
    KieClient,
    KieError,
)
from app.services import providers as provider_service
from app.services import video_models
from app.services.video_models import VideoInputError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/generate", tags=["generation"])


def get_kie_client() -> KieClient:
    """Build a client from whatever Kie.ai key is configured right now."""
    api_key, source = provider_service.resolve_key("kie")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail=(
                "Nenhuma chave da Kie.ai configurada. Cadastre uma na tela de "
                "Integrações antes de gerar vídeo."
            ),
        )

    logger.debug("Kie.ai client built with a key from %s", source)
    return KieClient(api_key)


def _translate(error: KieError) -> HTTPException:
    status = 401 if isinstance(error, KieAuthError) else 502
    if error.code == 402:
        status = 402
    elif error.code == 429:
        status = 429
    return HTTPException(status_code=status, detail=str(error))


@router.get("/catalog", response_model=GenerationCatalog)
async def get_catalog():
    """
    The model catalog with each model's parameter schema.

    The UI builds its controls from this, so a model added to the catalog shows
    up with the right fields without any frontend change.
    """
    credential = provider_service.describe_credential("kie")

    models: List[ModelSpec] = []
    categories: Dict[str, str] = {}

    for model_id in video_models.supported_models():
        model = video_models.get_model(model_id) or {}
        required = set(model.get("required") or [])

        fields = [
            FieldSpec(
                name=name,
                type=spec.get("type", "string"),
                item_type=spec.get("item_type"),
                enum=spec.get("enum"),
                default=spec.get("default"),
                max_length=spec.get("max_length"),
                max_items=spec.get("max_items"),
                minimum=spec.get("minimum"),
                maximum=spec.get("maximum"),
                description=spec.get("description", ""),
                required=name in required,
            )
            for name, spec in sorted((model.get("properties") or {}).items())
        ]

        category = model.get("category", "outros")
        categories[category] = model.get("category_label", category)

        models.append(
            ModelSpec(
                id=model_id,
                label=model.get("label", model_id),
                category=category,
                category_label=categories[category],
                docs_url=model.get("docs_url", ""),
                fields=fields,
                constraints=model.get("constraints") or {},
            )
        )

    return GenerationCatalog(
        configured=bool(credential["configured"]),
        models=models,
        categories=[{"id": key, "label": value} for key, value in sorted(categories.items())],
    )


@router.get("/credits", response_model=CreditsResponse)
async def get_credits():
    """Remaining Kie.ai credits, so the UI can show the budget before spending."""
    client = get_kie_client()
    try:
        credits = await client.get_credits()
    except KieError as exc:
        raise _translate(exc) from exc

    return CreditsResponse(credits=credits)


@router.post("/video", response_model=GenerateVideoResponse, status_code=202)
async def generate_video(payload: GenerateVideoRequest):
    """
    Queue a video generation. This spends credits on the configured account.

    Returns 202 with a task id — poll /generate/task/{task_id} for the result.
    """
    client = get_kie_client()

    try:
        task_input = video_models.build_input(payload.model, payload.values)
    except VideoInputError as exc:
        # Caught before any request goes out, so a bad payload costs nothing.
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        task_id = await client.create_task(
            payload.model, task_input, callback_url=payload.callback_url
        )
    except KieError as exc:
        raise _translate(exc) from exc

    return GenerateVideoResponse(
        task_id=task_id,
        model=payload.model,
        message="Geração na fila. Consulte o status pelo taskId.",
    )


@router.post("/download-url", response_model=DownloadUrlResponse)
async def get_download_url(payload: DownloadUrlRequest):
    """
    Mint a download link for a generated file.

    The URLs in a finished task are for viewing; this returns one that actually
    downloads. It expires quickly, so call it when the user clicks save rather
    than when the result is rendered.
    """
    client = get_kie_client()
    try:
        link = await client.get_download_url(payload.url)
    except KieError as exc:
        raise _translate(exc) from exc

    return DownloadUrlResponse(
        download_url=link, expires_in_minutes=DOWNLOAD_LINK_TTL_MINUTES
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Progress and result of a queued generation."""
    client = get_kie_client()

    try:
        task = await client.get_task(task_id)
    except KieError as exc:
        raise _translate(exc) from exc

    return TaskStatusResponse(
        task_id=task.task_id or task_id,
        model=task.model,
        state=task.state,
        finished=task.finished,
        succeeded=task.succeeded,
        progress=task.progress,
        result_urls=task.result_urls,
        credits_consumed=task.credits_consumed,
        cost_time_ms=task.cost_time_ms,
        fail_message=task.fail_message,
    )
