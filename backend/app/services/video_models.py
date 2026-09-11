"""
Schema-driven input building for Kie.ai video models.

Nothing about a model's parameters is written here. The catalog in
``app/data/kie_models.json`` is generated from Kie.ai's own published OpenAPI
docs (see ``scripts/fetch_kie_schemas.py``), and both the validation below and
the form the UI renders come from it. Adding a model means regenerating the
catalog, not writing code.

The catalog carries two kinds of rules:

- Per-field, from the schema: types, enums, defaults, string and array limits,
  numeric ranges.
- Cross-field, from the models' prose documentation: which references are
  mutually exclusive, which field requires another, and the upload "slot"
  budget. Those cannot be expressed in JSON Schema, so the generator encodes
  them under ``constraints`` with the source quoted.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "kie_models.json"

GEMINI_OMNI_FLASH = "google/gemini-omni-flash-1-1"

# Fields that hold references, in the order the slot budget counts them.
FIRST_FRAME_FIELD = "first_frame_url"


class VideoInputError(ValueError):
    """The requested generation input violates the model's published schema."""


@lru_cache(maxsize=1)
def load_catalog() -> Dict[str, Dict[str, Any]]:
    """The generated model catalog, read once per process."""
    try:
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.error("Model catalog missing at %s", CATALOG_PATH)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("Model catalog is not valid JSON: %s", exc)
        return {}


def supported_models() -> List[str]:
    return sorted(load_catalog().keys())


def get_model(model_id: str) -> Optional[Dict[str, Any]]:
    return load_catalog().get(model_id)


def require_model(model_id: str) -> Dict[str, Any]:
    model = get_model(model_id)
    if model is None:
        available = ", ".join(supported_models()) or "nenhum"
        raise VideoInputError(
            f"O modelo '{model_id}' não está no catálogo. Disponíveis: {available}."
        )
    return model


# ----------------------------------------------------------------------
# Per-field validation
# ----------------------------------------------------------------------
def _coerce_and_check(name: str, spec: Dict[str, Any], value: Any) -> Any:
    declared = spec.get("type", "string")

    if declared == "boolean":
        if not isinstance(value, bool):
            raise VideoInputError(f"'{name}' deve ser verdadeiro ou falso.")
        return value

    if declared == "integer":
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise VideoInputError(f"'{name}' deve ser um número inteiro.") from exc
        _check_range(name, spec, number)
        return number

    if declared == "number":
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise VideoInputError(f"'{name}' deve ser um número.") from exc
        _check_range(name, spec, number)
        return number

    if declared == "array":
        if not isinstance(value, (list, tuple)):
            raise VideoInputError(f"'{name}' deve ser uma lista.")
        items = [item for item in value if item not in (None, "")]
        max_items = spec.get("max_items")
        if max_items is not None and len(items) > max_items:
            raise VideoInputError(f"'{name}': no máximo {max_items} itens.")
        if spec.get("item_type") == "string":
            items = [str(item) for item in items]
        return items

    # Strings, including enum-constrained ones.
    text = str(value)
    enum = spec.get("enum")
    if enum and text not in enum:
        raise VideoInputError(
            f"'{name}' inválido: {text}. Use um de: {', '.join(enum)}."
        )
    max_length = spec.get("max_length")
    if max_length is not None and len(text) > max_length:
        raise VideoInputError(
            f"'{name}' tem {len(text)} caracteres; o limite é {max_length}."
        )
    return text


def _check_range(name: str, spec: Dict[str, Any], number: float) -> None:
    minimum = spec.get("minimum")
    maximum = spec.get("maximum")
    if minimum is not None and number < minimum:
        raise VideoInputError(f"'{name}' não pode ser menor que {minimum}.")
    if maximum is not None and number > maximum:
        raise VideoInputError(f"'{name}' não pode ser maior que {maximum}.")


def _check_enum_for_integer(name: str, spec: Dict[str, Any], value: Any) -> None:
    """Some enums are declared on integer fields; honour them too."""
    enum = spec.get("enum")
    if enum and str(value) not in enum:
        raise VideoInputError(
            f"'{name}' inválido: {value}. Use um de: {', '.join(enum)}."
        )


# ----------------------------------------------------------------------
# Cross-field constraints
# ----------------------------------------------------------------------
def _apply_constraints(model: Dict[str, Any], payload: Dict[str, Any]) -> None:
    constraints = model.get("constraints") or {}

    # "X must be provided together with Y"
    for field, prerequisite in (constraints.get("requires") or {}).items():
        if payload.get(field) and not payload.get(prerequisite):
            raise VideoInputError(
                f"'{field}' só pode ser usado junto com '{prerequisite}'."
            )

    # "first frame is mutually exclusive with these references"
    excluded = constraints.get("exclusive_with_first_frame") or []
    if payload.get(FIRST_FRAME_FIELD):
        clashing = [field for field in excluded if payload.get(field)]
        if clashing:
            raise VideoInputError(
                "Com o primeiro quadro definido, não dá para enviar também: "
                + ", ".join(clashing)
                + ". São caminhos alternativos."
            )

    # Duration range that lives in prose rather than in the schema.
    duration_range = constraints.get("duration_range")
    if duration_range and "duration" in payload:
        try:
            duration = int(payload["duration"])
        except (TypeError, ValueError):
            duration = None

        auto_value = constraints.get("duration_auto_value")
        if duration is not None and duration != auto_value:
            low, high = duration_range
            if not low <= duration <= high:
                extra = f" (ou {auto_value} para automático)" if auto_value is not None else ""
                raise VideoInputError(
                    f"Duração fora do intervalo: {duration}s. "
                    f"Use entre {low} e {high} segundos{extra}."
                )

    # Upload slot budget: each reference type costs a documented weight.
    slots = constraints.get("slots")
    if slots:
        weights: Dict[str, int] = slots.get("weights", {})
        used = sum(len(payload.get(field) or []) * weight for field, weight in weights.items())
        total = slots.get("total", 0)
        if used > total:
            detail = ", ".join(f"{field} vale {weight}" for field, weight in weights.items())
            raise VideoInputError(
                f"Referências demais: {used} de {total} vagas. ({detail}.)"
            )


# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------
def build_input(model_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate `values` against the model's schema and return the `input` object
    for createTask.

    Unknown keys are rejected rather than forwarded: a typo that the provider
    silently ignores would otherwise look like it worked and still cost credits.
    """
    model = require_model(model_id)
    properties: Dict[str, Any] = model.get("properties") or {}

    supplied = {
        key: value
        for key, value in (values or {}).items()
        if value is not None and value != "" and value != []
    }

    unknown = sorted(set(supplied) - set(properties))
    if unknown:
        raise VideoInputError(
            f"Parâmetros que {model['label']} não aceita: {', '.join(unknown)}."
        )

    payload: Dict[str, Any] = {}
    for name, value in supplied.items():
        spec = properties[name]
        checked = _coerce_and_check(name, spec, value)
        if spec.get("type") in ("integer", "number"):
            _check_enum_for_integer(name, spec, checked)
        payload[name] = checked

    for name in model.get("required") or []:
        if name not in payload:
            raise VideoInputError(
                f"'{name}' é obrigatório para {model['label']}."
            )

    _apply_constraints(model, payload)
    return payload


def default_values(model_id: str) -> Dict[str, Any]:
    """The model's own declared defaults — what the form should open with."""
    model = require_model(model_id)
    return {
        name: spec["default"]
        for name, spec in (model.get("properties") or {}).items()
        if "default" in spec
    }
