"""
Client for the Kie.ai job API.

Contract (verified against docs.kie.ai):

    POST /api/v1/jobs/createTask
        {"model": "...", "callBackUrl": "...", "input": {...}}
      -> {"code": 200, "msg": "success", "data": {"taskId": "..."}}

    GET /api/v1/jobs/recordInfo?taskId=...
      -> {"code": 200, "data": {"taskId", "model", "state", "param",
                                "resultJson", "failCode", "failMsg",
                                "costTime", "progress", "creditsConsumed"}}

Two shapes here are easy to get wrong and both are handled explicitly:

- The HTTP status is 200 even for errors; the real status is the body's
  ``code``. Trusting the HTTP status silently turns failures into successes.
- ``resultJson`` is a JSON *string*, not an object, so the result URLs need a
  second parse.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.kie.ai"
CREATE_TASK_PATH = "/api/v1/jobs/createTask"
TASK_DETAIL_PATH = "/api/v1/jobs/recordInfo"
CREDIT_PATH = "/api/v1/chat/credit"

REQUEST_TIMEOUT_SECONDS = 60.0

# States reported by recordInfo.
PENDING_STATES = frozenset({"waiting", "queuing", "generating"})
SUCCESS_STATE = "success"
FAILURE_STATE = "fail"


class KieError(RuntimeError):
    """A Kie.ai request failed. Carries the provider's own code and message."""

    def __init__(self, message: str, code: Optional[int] = None) -> None:
        super().__init__(message)
        self.code = code


class KieAuthError(KieError):
    """The API key was rejected."""


class KieTaskFailed(KieError):
    """The generation task itself failed on the provider's side."""


@dataclass
class KieTask:
    """A generation job as reported by recordInfo."""

    task_id: str
    state: str
    model: str = ""
    progress: float = 0.0
    result_urls: List[str] = field(default_factory=list)
    credits_consumed: Optional[float] = None
    cost_time_ms: Optional[int] = None
    fail_code: str = ""
    fail_message: str = ""

    @property
    def finished(self) -> bool:
        return self.state in (SUCCESS_STATE, FAILURE_STATE)

    @property
    def succeeded(self) -> bool:
        return self.state == SUCCESS_STATE

    @classmethod
    def from_payload(cls, data: Dict[str, Any]) -> "KieTask":
        return cls(
            task_id=str(data.get("taskId", "")),
            state=str(data.get("state", "")),
            model=str(data.get("model", "")),
            progress=_as_float(data.get("progress"), 0.0),
            result_urls=_parse_result_urls(data.get("resultJson")),
            credits_consumed=_as_optional_float(data.get("creditsConsumed")),
            cost_time_ms=_as_optional_int(data.get("costTime")),
            fail_code=str(data.get("failCode") or ""),
            fail_message=str(data.get("failMsg") or ""),
        )


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_optional_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_optional_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_result_urls(result_json: Any) -> List[str]:
    """`resultJson` arrives as a JSON string wrapping {"resultUrls": [...]}."""
    if not result_json:
        return []

    payload = result_json
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("Could not parse resultJson from Kie.ai")
            return []

    if not isinstance(payload, dict):
        return []

    urls = payload.get("resultUrls")
    if isinstance(urls, list):
        return [str(u) for u in urls if u]
    return []


class KieClient:
    """Thin async client over the Kie.ai job endpoints."""

    def __init__(self, api_key: str, base_url: str = BASE_URL) -> None:
        if not api_key:
            raise KieAuthError("Nenhuma chave da Kie.ai configurada.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Response handling
    # ------------------------------------------------------------------
    @staticmethod
    def _unwrap(response: httpx.Response) -> Dict[str, Any]:
        """Read the envelope, raising on the body's own error code."""
        try:
            payload = response.json()
        except ValueError as exc:
            raise KieError(
                f"A Kie.ai respondeu em formato inesperado (HTTP {response.status_code})."
            ) from exc

        if not isinstance(payload, dict):
            raise KieError("A Kie.ai respondeu em formato inesperado.")

        code = payload.get("code")
        if code in (401, 403) or response.status_code in (401, 403):
            raise KieAuthError(
                "A Kie.ai recusou a chave. Gere uma nova em kie.ai/api-key.", code=401
            )

        if code == 402:
            raise KieError("Sua conta na Kie.ai está sem créditos.", code=402)

        if code == 429:
            raise KieError("Limite de requisições da Kie.ai atingido. Tente em instantes.", code=429)

        if code not in (200, 0, None):
            detail = str(payload.get("msg") or payload.get("message") or "").strip()
            raise KieError(
                f"A Kie.ai recusou a requisição (código {code})."
                + (f" {detail}" if detail else ""),
                code=code if isinstance(code, int) else None,
            )

        if response.status_code >= 400:
            raise KieError(f"A Kie.ai respondeu HTTP {response.status_code}.")

        data = payload.get("data")
        return data if isinstance(data, dict) else {}

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.request(method, url, headers=self._headers, **kwargs)
        except httpx.TimeoutException as exc:
            raise KieError("A Kie.ai demorou demais para responder.") from exc
        except httpx.HTTPError as exc:
            raise KieError("Não consegui alcançar a Kie.ai. Verifique sua conexão.") from exc

        return self._unwrap(response)

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------
    async def get_credits(self) -> float:
        """Remaining credits on the account. Also doubles as a key check."""
        url = f"{self.base_url}{CREDIT_PATH}"
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.get(url, headers=self._headers)
        except httpx.HTTPError as exc:
            raise KieError("Não consegui alcançar a Kie.ai.") from exc

        # This endpoint returns the number directly in `data`, not an object.
        try:
            payload = response.json()
        except ValueError as exc:
            raise KieError("A Kie.ai respondeu em formato inesperado.") from exc

        code = payload.get("code") if isinstance(payload, dict) else None
        if code in (401, 403):
            raise KieAuthError("A Kie.ai recusou a chave.", code=401)
        if code not in (200, 0, None):
            raise KieError(f"A Kie.ai respondeu com o código {code}.", code=code)

        return _as_float(payload.get("data"), 0.0)

    async def create_task(
        self,
        model: str,
        task_input: Dict[str, Any],
        callback_url: Optional[str] = None,
    ) -> str:
        """Queue a generation job. Returns the task id."""
        body: Dict[str, Any] = {"model": model, "input": task_input}
        if callback_url:
            body["callBackUrl"] = callback_url

        data = await self._request("POST", CREATE_TASK_PATH, json=body)
        task_id = data.get("taskId")
        if not task_id:
            raise KieError("A Kie.ai aceitou o pedido mas não devolveu um taskId.")

        logger.info("Kie.ai task created: %s (model=%s)", task_id, model)
        return str(task_id)

    async def get_task(self, task_id: str) -> KieTask:
        """Current state of a job."""
        data = await self._request("GET", TASK_DETAIL_PATH, params={"taskId": task_id})
        if not data:
            raise KieError(f"A Kie.ai não conhece a tarefa '{task_id}'.")
        return KieTask.from_payload(data)

    async def wait_for_task(
        self,
        task_id: str,
        poll_interval_seconds: float = 5.0,
        timeout_seconds: float = 900.0,
    ) -> KieTask:
        """
        Poll until the job finishes. Raises KieTaskFailed if it fails.

        Prefer a callBackUrl in production; this exists for local runs and for
        the CLI-style flow where there is nothing public to call back to.
        """
        waited = 0.0
        while waited < timeout_seconds:
            task = await self.get_task(task_id)

            if task.succeeded:
                return task

            if task.state == FAILURE_STATE:
                raise KieTaskFailed(
                    task.fail_message or "A geração falhou na Kie.ai.",
                    code=_as_optional_int(task.fail_code),
                )

            await asyncio.sleep(poll_interval_seconds)
            waited += poll_interval_seconds

        raise KieError(
            f"A tarefa {task_id} passou de {int(timeout_seconds)}s sem terminar. "
            "Ela pode continuar rodando — consulte pelo taskId."
        )
