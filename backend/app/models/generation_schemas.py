"""Request/response schemas for AI video generation."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.services.video_models import (
    GEMINI_OMNI_FLASH,
    OMNI_ASPECT_RATIOS,
    OMNI_DURATIONS,
    OMNI_RESOLUTIONS,
)


class VideoClip(BaseModel):
    url: str = Field(..., description="Publicly reachable video URL, max 100MB / 30s")
    start: float = Field(0, ge=0, description="Trim start, in seconds")
    ends: float = Field(..., gt=0, description="Trim end, in seconds; window max 10s")


class GenerateVideoRequest(BaseModel):
    model: str = Field(GEMINI_OMNI_FLASH, description="Kie.ai model id")
    prompt: str = Field(..., min_length=1, max_length=20000)
    duration: str = Field("8", description=f"One of {', '.join(OMNI_DURATIONS)} seconds")
    aspect_ratio: str = Field("9:16", description=f"One of {', '.join(OMNI_ASPECT_RATIOS)}")
    resolution: str = Field("720p", description=f"One of {', '.join(OMNI_RESOLUTIONS)}")
    image_urls: Optional[List[str]] = Field(None, description="Reference images, max 7")
    first_frame_url: Optional[str] = Field(
        None, description="Opening frame; excludes every other reference"
    )
    last_frame_url: Optional[str] = Field(None, description="Closing frame; needs first_frame_url")
    audio_ids: Optional[List[str]] = Field(None, description="Ids from gemini-omni-audio, max 3")
    video_list: Optional[List[VideoClip]] = Field(None, description="Reference clip, max 1")
    character_ids: Optional[List[str]] = Field(
        None, description="Ids from gemini-omni-character"
    )
    seed: Optional[int] = Field(None, ge=0, le=2147483647)
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
    expires_in_minutes: int = Field(
        ..., description="The link stops working after this long"
    )


class CreditsResponse(BaseModel):
    credits: float
    provider: str = "kie"


class GenerationModelInfo(BaseModel):
    id: str
    label: str
    implemented: bool
    durations: List[str] = []
    aspect_ratios: List[str] = []
    resolutions: List[str] = []
    notes: str = ""


class GenerationCapabilities(BaseModel):
    configured: bool
    models: List[GenerationModelInfo]
    options: Dict[str, Any] = {}
