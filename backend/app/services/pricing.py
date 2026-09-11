"""
Cost estimation for Kie.ai generations.

Prices come from `app/data/kie_pricing.json`, transcribed from each model's
page on kie.ai. Two shapes exist and they are not interchangeable:

- **Per second** (Wan, all Seedance): credits = rate x seconds, where the rate
  depends on resolution and on whether a reference video was supplied. When it
  was, the billed duration is *input + output*, not just output — so an
  estimate without knowing the input length is a lower bound.
- **Per generation** (Gemini Omni): a flat price per duration/resolution pair,
  and a single flat price when a video is supplied, regardless of duration.

Every estimate says which assumptions it made, because guessing silently is
how someone ends up surprised by a bill.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PRICING_PATH = Path(__file__).resolve().parents[1] / "data" / "kie_pricing.json"

VIDEO_REFERENCE_FIELDS = ("video_list", "reference_video_urls")


@lru_cache(maxsize=1)
def load_pricing() -> Dict[str, Any]:
    try:
        return json.loads(PRICING_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("Pricing table unavailable: %s", exc)
        return {"credit_usd": 0.005, "models": {}}


def credit_usd() -> float:
    return float(load_pricing().get("credit_usd", 0.005))


def get_model_pricing(model_id: str) -> Optional[Dict[str, Any]]:
    return load_pricing().get("models", {}).get(model_id)


def _has_video_input(values: Dict[str, Any]) -> bool:
    return any(values.get(field) for field in VIDEO_REFERENCE_FIELDS)


def estimate(model_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimate what one generation costs.

    Returns credits, the USD equivalent, and `assumptions` — the things the
    caller should read before treating the number as a budget.
    """
    pricing = get_model_pricing(model_id)
    if not pricing:
        return {
            "available": False,
            "reason": "Não tenho a tabela de preços deste modelo.",
            "credits": None,
            "usd": None,
            "assumptions": [],
        }

    with_video = _has_video_input(values)
    resolution = str(values.get("resolution") or "")
    assumptions: List[str] = []

    if pricing["mode"] == "per_generation":
        table = pricing["with_video"] if with_video else pricing["no_video"]

        if with_video:
            credits = table.get(resolution)
            if credits is None:
                return _unknown(resolution, pricing)
            assumptions.append("Com vídeo de referência o preço é fixo, não depende da duração.")
        else:
            by_duration = table.get(resolution)
            if by_duration is None:
                return _unknown(resolution, pricing)
            duration = str(values.get("duration") or "")
            credits = by_duration.get(duration)
            if credits is None:
                return {
                    "available": False,
                    "reason": f"Sem preço para {duration or '—'}s em {resolution}.",
                    "credits": None,
                    "usd": None,
                    "assumptions": [],
                }

        return _result(credits, assumptions, pricing)

    # Per-second models.
    rates = pricing.get("per_second", {}).get(resolution)
    if not rates:
        return _unknown(resolution, pricing)

    rate = rates["with_video"] if with_video else rates["no_video"]

    try:
        seconds = float(values.get("duration"))
    except (TypeError, ValueError):
        return {
            "available": False,
            "reason": "Defina a duração para estimar o custo.",
            "credits": None,
            "usd": None,
            "assumptions": [],
        }

    if seconds < 0:
        # -1 means the model chooses. No way to price that up front.
        return {
            "available": False,
            "reason": "Com duração automática (-1) o custo só é conhecido no fim.",
            "credits": None,
            "usd": None,
            "assumptions": [],
        }

    credits = rate * seconds

    if with_video:
        assumptions.append(
            "Com vídeo de referência a cobrança é (entrada + saída) x preço. "
            "Este valor conta só a saída, então é o mínimo."
        )

    return _result(credits, assumptions, pricing)


def _unknown(resolution: str, pricing: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "available": False,
        "reason": f"Sem preço publicado para a resolução {resolution or '—'}.",
        "credits": None,
        "usd": None,
        "assumptions": [],
        "source_url": pricing.get("source_url"),
    }


def _result(credits: float, assumptions: List[str], pricing: Dict[str, Any]) -> Dict[str, Any]:
    assumptions = list(assumptions)
    if pricing.get("note"):
        assumptions.append(pricing["note"])
    assumptions.append(
        "Preços da Kie.ai estão em beta e mudam; confira na página do modelo "
        "antes de fechar orçamento."
    )

    return {
        "available": True,
        "reason": "",
        "credits": round(credits, 1),
        "usd": round(credits * credit_usd(), 3),
        "assumptions": assumptions,
        "source_url": pricing.get("source_url"),
    }


def rate_table(model_id: str) -> Dict[str, Any]:
    """The model's published rates, for showing a price list in the UI."""
    pricing = get_model_pricing(model_id)
    if not pricing:
        return {}

    return {
        "mode": pricing["mode"],
        "note": pricing.get("note", ""),
        "source_url": pricing.get("source_url", ""),
        "per_second": pricing.get("per_second", {}),
        "no_video": pricing.get("no_video", {}),
        "with_video": pricing.get("with_video", {}),
    }
