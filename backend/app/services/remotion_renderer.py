import asyncio
import uuid
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class RemotionRenderJob:
    """Represents a Remotion render job"""
    def __init__(self, job_id: str, composition_id: str, props: Dict[str, Any]):
        self.job_id = job_id
        self.composition_id = composition_id
        self.props = props
        self.status = "pending"
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.output_url: Optional[str] = None
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "composition_id": self.composition_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output_url": self.output_url,
            "error": self.error,
        }


class RemotionRenderService:
    """Service for managing Remotion video rendering"""

    def __init__(self):
        self.jobs: Dict[str, RemotionRenderJob] = {}

    async def create_render_job(
        self,
        composition_id: str,
        duration_in_frames: int,
        fps: int,
        width: int,
        height: int,
        props: Optional[Dict[str, Any]] = None,
    ) -> RemotionRenderJob:
        """Create a new render job"""
        job_id = str(uuid.uuid4())

        job = RemotionRenderJob(
            job_id=job_id,
            composition_id=composition_id,
            props={
                "durationInFrames": duration_in_frames,
                "fps": fps,
                "width": width,
                "height": height,
                **(props or {}),
            },
        )

        self.jobs[job_id] = job

        # Simulate async rendering
        asyncio.create_task(self._simulate_render(job_id))

        logger.info(f"Created render job: {job_id} for composition: {composition_id}")
        return job

    async def _simulate_render(self, job_id: str) -> None:
        """Simulate the rendering process"""
        job = self.jobs.get(job_id)
        if not job:
            return

        try:
            job.status = "processing"

            # Simulate rendering delay
            await asyncio.sleep(5)

            # Generate mock output URL
            job.output_url = f"https://example.com/videos/{job_id}.mp4"
            job.status = "completed"
            job.completed_at = datetime.now()

            logger.info(f"Completed render job: {job_id}")
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Failed to render job {job_id}: {e}")

    async def get_job_status(self, job_id: str) -> Optional[RemotionRenderJob]:
        """Get the status of a render job"""
        return self.jobs.get(job_id)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a render job"""
        job = self.jobs.get(job_id)
        if job and job.status in ["pending", "processing"]:
            job.status = "cancelled"
            job.completed_at = datetime.now()
            logger.info(f"Cancelled render job: {job_id}")
            return True
        return False

    def get_all_jobs(self) -> Dict[str, RemotionRenderJob]:
        """Get all render jobs"""
        return self.jobs.copy()


# Global instance
remotion_render_service = RemotionRenderService()
