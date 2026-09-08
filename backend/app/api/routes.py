import os
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional
import uuid

from app.models.schemas import (
    ProjectCreate,
    ProjectResponse,
    EmotionalAnalysisResponse,
    VideoAnalysisResponse,
)
from app.services.ai_analyzer import AIAnalyzer, MissingCredentialError
from app.services.video_processor import VideoProcessor
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["video_editor"])

settings = get_settings()
video_processor = VideoProcessor()


def get_ai_analyzer() -> AIAnalyzer:
    """
    Resolve the analyzer from whatever credential is configured right now.

    Built per request (instead of at import time) so a key saved in the
    Integrações screen takes effect without restarting the server.
    """
    try:
        return AIAnalyzer.from_configuration()
    except MissingCredentialError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

# In-memory storage for demo (replace with database in production)
projects = {}


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    vibe: str = Form(...),
    description: Optional[str] = Form(None),
):
    """
    Upload video and initialize project with emotional vibe.
    """
    try:
        # Validate file
        if not file.filename.endswith(tuple(settings.supported_formats)):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Supported: {settings.supported_formats}",
            )

        file_size = await file.seek(0, 2)
        await file.seek(0)

        if file_size > settings.max_file_size:
            raise HTTPException(status_code=413, detail="File too large")

        # Save file
        os.makedirs(settings.upload_directory, exist_ok=True)
        project_id = str(uuid.uuid4())
        file_path = os.path.join(settings.upload_directory, f"{project_id}.mp4")

        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)

        # Get video metadata
        metadata = await video_processor.get_video_metadata(file_path)

        # Analyze with AI
        analysis = await get_ai_analyzer().analyze_emotional_vibe(vibe, metadata)

        # Store project
        projects[project_id] = {
            "id": project_id,
            "filename": file.filename,
            "video_path": file_path,
            "vibe": vibe,
            "description": description,
            "metadata": metadata,
            "analysis": analysis,
            "status": "analyzing",
        }

        return {
            "project_id": project_id,
            "message": "Video uploaded successfully",
            "metadata": metadata,
            "emotional_analysis": analysis,
        }

    except HTTPException:
        # Already a meaningful client error (bad format, missing API key…).
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}")
async def get_project(project_id: str):
    """Get project details and current analysis."""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    return projects[project_id]


@router.post("/edit/{project_id}")
async def edit_video(project_id: str, background_tasks: BackgroundTasks):
    """
    Start automated video editing based on emotional analysis.
    """
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    project = projects[project_id]
    video_path = project["video_path"]

    try:
        # Queue editing tasks
        background_tasks.add_task(
            process_video_editing, project_id, video_path, project["analysis"]
        )

        return {
            "project_id": project_id,
            "status": "editing_started",
            "message": "Video editing in progress",
        }

    except Exception as e:
        logger.error(f"Editing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/edit/{project_id}/status")
async def get_edit_status(project_id: str):
    """Get editing progress."""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    project = projects[project_id]
    return {
        "project_id": project_id,
        "status": project.get("status", "pending"),
        "progress": project.get("progress", 0),
        "output_path": project.get("output_path"),
    }


@router.post("/analyze-references")
async def analyze_references(
    project_id: str = Form(...), vibe: str = Form(...)
):
    """Analyze reference images/videos to suggest aesthetic."""
    try:
        references = [
            "dark luxury aesthetic with gold accents",
            "cinematic color grading",
            "minimal typography",
        ]

        aesthetic = await get_ai_analyzer().suggest_aesthetic_style(references, vibe)

        return {
            "project_id": project_id,
            "aesthetic_suggestion": aesthetic,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{project_id}")
async def download_video(project_id: str):
    """Download edited video."""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    project = projects[project_id]
    output_path = project.get("output_path")

    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Edited video not ready")

    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"edited_{project['filename']}",
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


async def process_video_editing(project_id: str, video_path: str, analysis: dict):
    """Background task to process video editing."""
    try:
        projects[project_id]["status"] = "removing_silence"
        projects[project_id]["progress"] = 25

        # Remove silence
        silence_removed = await video_processor.remove_silence(video_path)

        projects[project_id]["status"] = "color_grading"
        projects[project_id]["progress"] = 50

        # Apply color grading
        color_params = analysis.get("color_grading", {})
        color_graded = await video_processor.apply_basic_color_grading(
            silence_removed, color_params
        )

        projects[project_id]["status"] = "scaling"
        projects[project_id]["progress"] = 75

        # Scale for TikTok
        final_video = await video_processor.scale_for_platform(color_graded, "tiktok")

        projects[project_id]["status"] = "completed"
        projects[project_id]["progress"] = 100
        projects[project_id]["output_path"] = final_video

    except Exception as e:
        logger.error(f"Processing error: {e}")
        projects[project_id]["status"] = "error"
        projects[project_id]["error"] = str(e)
