from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    emotional_vibe: str = Field(..., description="luxury, energy, drama, elegance, etc")


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    emotional_vibe: str
    estimated_duration: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class EmotionalAnalysisResponse(BaseModel):
    primary_emotion: str
    secondary_emotions: List[str]
    intensity: float
    recommended_pacing: str
    color_temperature: str
    suggested_music_mood: str


class VideoAnalysisResponse(BaseModel):
    emotional_analysis: Dict
    visual_style: str
    detected_aesthetic: str
    color_palette: List[str]
    pacing_analysis: Dict
    retention_score: Optional[float]

    class Config:
        from_attributes = True


class EditingTaskResponse(BaseModel):
    id: int
    project_id: int
    task_type: str
    status: str
    progress: float
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    webhook_url: Optional[str] = None


class ImageGenerationResponse(BaseModel):
    request_id: str
    status: str


class ProcessingStatusResponse(BaseModel):
    project_id: int
    overall_progress: float
    current_task: str
    tasks: List[EditingTaskResponse]
    estimated_time_remaining: Optional[int]
