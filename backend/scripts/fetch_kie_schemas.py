#!/usr/bin/env python3
"""
Regenerate app/data/kie_models.json from Kie.ai's published OpenAPI docs.

Run it when Kie.ai adds a model or changes a schema:

    python backend/scripts/fetch_kie_schemas.py

Why this exists: hand-copying a model's parameters into code goes stale and
invites typos, and every model has a different parameter set. Reading the
published schema means the form and the validation both come from the source.

Two things the published schema does NOT give us, both handled below:

1. Wrong declared types. Wan 3.0 declares `first_frame_url` and the
   `reference_*_urls` items as `type: object` with empty properties, but every
   example in the same document passes a plain URL string. COERCE_TO_STRING
   fixes those back to strings.
2. Cross-field rules. "First frame and reference images are mutually
   exclusive", the 7-slot upload budget, Seedance's 4-30s duration range —
   all of that is prose in the description, not schema. CONSTRAINTS encodes
   it, with the source quoted next to each entry.
"""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict

import yaml

DOCS_BASE = "https://docs.kie.ai"
OUTPUT = Path(__file__).resolve().parents[1] / "app" / "data" / "kie_models.json"

# model id -> (docs path, display label, category)
MODELS = [
    ("google/gemini-omni-flash-1-1", "market/google/gemini-omni-flash-1-1",
     "Gemini Omni 1.1 Flash", "referencia-video"),
    ("wan/3-0-video", "market/wan/3-0-video",
     "Wan 3.0", "referencia-video"),
    ("bytedance/seedance-2-5", "market/bytedance/seedance-2-5",
     "Seedance 2.5", "texto-video"),
    ("bytedance/seedance-2", "market/bytedance/seedance-2",
     "Seedance 2.0", "texto-video"),
    ("bytedance/seedance-2-fast", "market/bytedance/seedance-2-fast",
     "Seedance 2.0 Fast", "texto-video"),
    # Seedream is ByteDance's image family. Note 4.5 uses a dot in its id
    # while 5 uses dashes — copy them exactly.
    ("seedream/5-pro-text-to-image", "market/seedream/5-pro-text-to-image",
     "Seedream 5 Pro", "texto-imagem"),
    ("seedream/5-lite-text-to-image", "market/seedream/5-lite-text-to-image",
     "Seedream 5 Lite", "texto-imagem"),
    ("seedream/4.5-text-to-image", "market/seedream/4-5-text-to-image",
     "Seedream 4.5", "texto-imagem"),
    ("seedream/5-pro-image-to-image", "market/seedream/5-pro-image-to-image",
     "Seedream 5 Pro — editar", "editar-imagem"),
    ("seedream/5-lite-image-to-image", "market/seedream-5-lite-image-to-image",
     "Seedream 5 Lite — editar", "editar-imagem"),
    ("seedream/4.5-edit", "market/seedream/4-5-edit",
     "Seedream 4.5 — editar", "editar-imagem"),
]

CATEGORY_LABELS = {
    "texto-video": "Texto → Vídeo",
    "referencia-video": "Referência → Vídeo",
    "texto-imagem": "Texto → Imagem",
    "editar-imagem": "Editar imagem",
}

# Fields the docs declare as `object` but whose own examples pass a URL string.
COERCE_TO_STRING = {"first_frame_url", "last_frame_url"}
COERCE_ITEMS_TO_STRING = re.compile(r"^reference_\w+_urls$")

# Cross-field rules, quoted from each model's own description text.
CONSTRAINTS: Dict[str, Dict[str, Any]] = {
    "google/gemini-omni-flash-1-1": {
        # "This field is mutually exclusive with the first-frame image
        #  (first_frame_url) and cannot be provided at the same time."
        "exclusive_with_first_frame": [
            "image_urls", "audio_ids", "video_list", "character_ids",
        ],
        # "The last-frame image cannot be used alone and must be provided
        #  together with the first-frame image."
        "requires": {"last_frame_url": "first_frame_url"},
        # "(Images) + (Videos x 2) + (Character IDs) <= 7"
        "slots": {
            "total": 7,
            "weights": {"image_urls": 1, "video_list": 2, "character_ids": 1},
        },
    },
    "wan/3-0-video": {
        # "Cannot be provided together with `reference_*_urls`."
        "exclusive_with_first_frame": [
            "reference_image_urls", "reference_video_urls",
            "reference_audio_urls", "reference_file_urls", "reference_link_urls",
        ],
        "requires": {"last_frame_url": "first_frame_url"},
        # "Without video input, the range is [2, 30]. ... Pass `-1` to use an
        #  intelligent duration determined by the model."
        "duration_range": [2, 30],
        "duration_auto_value": -1,
    },
}

# Seedance models share one rule set: "Image-to-Video (First Frame),
# Image-to-Video (First & Last Frames), and Multimodal Reference-to-Video ...
# are three mutually exclusive scenarios". Duration: "4-30 seconds", with -1
# meaning the model picks.
SEEDANCE_CONSTRAINTS = {
    "exclusive_with_first_frame": [
        "reference_image_urls", "reference_video_urls", "reference_audio_urls",
    ],
    "requires": {"last_frame_url": "first_frame_url"},
    "duration_range": [4, 30],
    "duration_auto_value": -1,
}
for _seedance in ("bytedance/seedance-2-5", "bytedance/seedance-2",
                  "bytedance/seedance-2-fast"):
    CONSTRAINTS[_seedance] = dict(SEEDANCE_CONSTRAINTS)


def fetch_markdown(path: str, tries: int = 5) -> str:
    """The docs site sometimes serves an HTML shell; retry until we get the md."""
    url = f"{DOCS_BASE}/{path}.md"
    for attempt in range(tries):
        request = urllib.request.Request(url, headers={"User-Agent": "kie-schema-sync"})
        body = urllib.request.urlopen(request, timeout=45).read().decode("utf-8", "replace")
        if body.lstrip().startswith("#"):
            return body
        time.sleep(3 + attempt * 2)
    raise RuntimeError(f"Only got the HTML shell for {path}")


def convert_property(name: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    declared = meta.get("type", "string")

    if name in COERCE_TO_STRING and declared == "object":
        declared = "string"

    entry: Dict[str, Any] = {"type": declared}

    if "enum" in meta:
        entry["enum"] = [str(value) for value in meta["enum"]]
    if "default" in meta:
        entry["default"] = meta["default"]
    if "maxLength" in meta:
        entry["max_length"] = meta["maxLength"]
    if "maxItems" in meta:
        entry["max_items"] = meta["maxItems"]
    if "minimum" in meta:
        entry["minimum"] = meta["minimum"]
    if "maximum" in meta:
        entry["maximum"] = meta["maximum"]

    if declared == "array":
        item_type = (meta.get("items") or {}).get("type", "string")
        if COERCE_ITEMS_TO_STRING.match(name) and item_type == "object":
            item_type = "string"
        entry["item_type"] = item_type

    description = " ".join(str(meta.get("description", "")).split())
    if description:
        entry["description"] = description[:500]

    return entry


def extract(model_id: str, path: str, label: str, category: str) -> Dict[str, Any]:
    markdown = fetch_markdown(path)

    block = re.search(r"```yaml\n(.*?)\n```", markdown, re.S)
    if not block:
        raise RuntimeError(f"No OpenAPI block in {path}")

    spec = yaml.safe_load(block.group(1))
    request_body = spec["paths"]["/api/v1/jobs/createTask"]["post"]["requestBody"]
    schema = request_body["content"]["application/json"]["schema"]
    task_input = schema["properties"]["input"]

    properties = {
        name: convert_property(name, meta)
        for name, meta in (task_input.get("properties") or {}).items()
    }

    required = list(task_input.get("required") or [])
    # Every one of these models needs a prompt; only Gemini Omni declares it.
    if "prompt" in properties and "prompt" not in required:
        required.append("prompt")

    return {
        "id": model_id,
        "label": label,
        "category": category,
        "category_label": CATEGORY_LABELS.get(category, category),
        "required": required,
        "properties": properties,
        "constraints": CONSTRAINTS.get(model_id, {}),
        "docs_url": f"{DOCS_BASE}/{path}",
    }


def main() -> int:
    catalog: Dict[str, Any] = {}

    for model_id, path, label, category in MODELS:
        try:
            catalog[model_id] = extract(model_id, path, label, category)
        except Exception as exc:  # noqa: BLE001 - operational script
            print(f"FAILED {model_id}: {exc}", file=sys.stderr)
            return 1

        count = len(catalog[model_id]["properties"])
        print(f"ok  {model_id:32s} {count:2d} parâmetros")
        time.sleep(3)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"\nEscrito: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
