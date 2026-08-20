import logging
from typing import Optional

import fal_client

logger = logging.getLogger(__name__)


class FalService:
    """Submits image/video generation jobs to fal.ai models (e.g. nano-banana-2)."""

    def __init__(self, api_key: str):
        if api_key:
            fal_client.api_key = api_key

    async def submit_image_generation(
        self,
        prompt: str,
        model: str = "fal-ai/nano-banana-2",
        webhook_url: Optional[str] = None,
    ) -> str:
        """Queues an image generation job and returns the fal.ai request_id."""
        handler = await fal_client.submit_async(
            model,
            arguments={"prompt": prompt},
            webhook_url=webhook_url,
        )
        return handler.request_id

    async def get_status(self, request_id: str, model: str = "fal-ai/nano-banana-2") -> dict:
        """Polls the status of a queued fal.ai job."""
        status = await fal_client.status_async(model, request_id, with_logs=False)
        return status

    async def get_result(self, request_id: str, model: str = "fal-ai/nano-banana-2") -> dict:
        """Fetches the final result of a completed fal.ai job."""
        result = await fal_client.result_async(model, request_id)
        return result
