import logging
from typing import Any, Dict

import fal_client

logger = logging.getLogger(__name__)


class FalService:
    """Thin wrapper around the fal.ai client for AI model inference."""

    def __init__(self, api_key: str):
        self.client = fal_client.SyncClient(key=api_key)

    def run(self, model: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Runs a fal.ai model synchronously and returns its output."""
        return self.client.run(model, arguments=arguments)
