"""
Input building and validation for Kie.ai video models.

Every rule here comes from the model's published schema. Validating locally
matters because a rejected request still costs a round trip, and a malformed
one can cost credits — it is cheaper to fail here with a clear message.

Currently implemented: Gemini Omni 1.1 Flash (google/gemini-omni-flash-1-1).
The other catalogued models share the createTask/recordInfo envelope but have
their own input schemas, so each needs its own builder before being exposed.
"""

from typing import Any, Dict, List, Optional

GEMINI_OMNI_FLASH = "google/gemini-omni-flash-1-1"

SUPPORTED_MODELS = (GEMINI_OMNI_FLASH,)

# --- Gemini Omni 1.1 Flash schema constants ---------------------------------
OMNI_DURATIONS = ("4", "6", "8", "10")
OMNI_ASPECT_RATIOS = ("16:9", "9:16")
OMNI_RESOLUTIONS = ("360p", "720p", "1080p", "4k")
OMNI_PROMPT_MAX_LENGTH = 20000
OMNI_SEED_MAX = 2147483647

# The provider budgets uploads in "slots": images 1 each, videos 2 each,
# character ids 1 each, with a total of 7.
OMNI_TOTAL_SLOTS = 7
OMNI_MAX_IMAGES = 7
OMNI_MAX_VIDEOS = 1
OMNI_MAX_AUDIO_IDS = 3
OMNI_MAX_CHARACTER_IDS = 3
OMNI_MAX_CLIP_SECONDS = 10.0

# first_frame_url cannot be combined with any of these.
OMNI_FIRST_FRAME_CONFLICTS = ("image_urls", "audio_ids", "video_list", "character_ids")


class VideoInputError(ValueError):
    """The requested generation input violates the model's schema."""


def build_gemini_omni_input(
    prompt: str,
    duration: str = "8",
    aspect_ratio: str = "9:16",
    resolution: str = "720p",
    image_urls: Optional[List[str]] = None,
    first_frame_url: Optional[str] = None,
    last_frame_url: Optional[str] = None,
    audio_ids: Optional[List[str]] = None,
    video_list: Optional[List[Dict[str, Any]]] = None,
    character_ids: Optional[List[str]] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build and validate the `input` object for Gemini Omni 1.1 Flash.

    Defaults lean vertical (9:16) because the editor targets Reels and TikTok.
    """
    prompt = (prompt or "").strip()
    if not prompt:
        raise VideoInputError("Descreva o vídeo: o prompt não pode ficar vazio.")
    if len(prompt) > OMNI_PROMPT_MAX_LENGTH:
        raise VideoInputError(
            f"O prompt tem {len(prompt)} caracteres; o limite é {OMNI_PROMPT_MAX_LENGTH}."
        )

    duration = str(duration)
    if duration not in OMNI_DURATIONS:
        raise VideoInputError(
            f"Duração inválida: {duration}s. Use uma de {', '.join(OMNI_DURATIONS)} segundos."
        )

    if aspect_ratio not in OMNI_ASPECT_RATIOS:
        raise VideoInputError(
            f"Proporção inválida: {aspect_ratio}. Use {' ou '.join(OMNI_ASPECT_RATIOS)}."
        )

    if resolution not in OMNI_RESOLUTIONS:
        raise VideoInputError(
            f"Resolução inválida: {resolution}. Use uma de {', '.join(OMNI_RESOLUTIONS)}."
        )

    image_urls = list(image_urls or [])
    audio_ids = list(audio_ids or [])
    video_list = list(video_list or [])
    character_ids = list(character_ids or [])

    payload: Dict[str, Any] = {
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
    }

    if seed is not None:
        if not 0 <= seed <= OMNI_SEED_MAX:
            raise VideoInputError(f"Seed fora do intervalo (0 a {OMNI_SEED_MAX}).")
        payload["seed"] = seed

    # --- first/last frame rules ---
    if last_frame_url and not first_frame_url:
        raise VideoInputError(
            "O último quadro só pode ser usado junto com o primeiro quadro."
        )

    if first_frame_url:
        conflicting = {
            "image_urls": image_urls,
            "audio_ids": audio_ids,
            "video_list": video_list,
            "character_ids": character_ids,
        }
        used = [name for name in OMNI_FIRST_FRAME_CONFLICTS if conflicting[name]]
        if used:
            raise VideoInputError(
                "Quando você define o primeiro quadro, não dá para enviar também: "
                + ", ".join(used)
                + ". Escolha um caminho ou outro."
            )

        payload["first_frame_url"] = first_frame_url
        if last_frame_url:
            payload["last_frame_url"] = last_frame_url
        return payload

    # --- multimodal reference rules ---
    if len(image_urls) > OMNI_MAX_IMAGES:
        raise VideoInputError(f"No máximo {OMNI_MAX_IMAGES} imagens de referência.")
    if len(video_list) > OMNI_MAX_VIDEOS:
        raise VideoInputError(f"No máximo {OMNI_MAX_VIDEOS} vídeo de referência.")
    if len(audio_ids) > OMNI_MAX_AUDIO_IDS:
        raise VideoInputError(f"No máximo {OMNI_MAX_AUDIO_IDS} áudios de referência.")
    if video_list and len(character_ids) > OMNI_MAX_CHARACTER_IDS:
        raise VideoInputError(
            f"Com um vídeo de referência, no máximo {OMNI_MAX_CHARACTER_IDS} personagens."
        )

    slots = len(image_urls) + (len(video_list) * 2) + len(character_ids)
    if slots > OMNI_TOTAL_SLOTS:
        raise VideoInputError(
            f"Referências demais: {slots} de {OMNI_TOTAL_SLOTS} vagas. "
            "Cada imagem e personagem ocupa 1 vaga, cada vídeo ocupa 2."
        )

    for index, clip in enumerate(video_list, start=1):
        payload_clip = _validate_clip(clip, index)
        clip.update(payload_clip)

    if image_urls:
        payload["image_urls"] = image_urls
    if audio_ids:
        payload["audio_ids"] = audio_ids
    if video_list:
        payload["video_list"] = video_list
    if character_ids:
        payload["character_ids"] = character_ids

    return payload


def _validate_clip(clip: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Each reference clip needs url/start/ends, with a window of up to 10s."""
    if not isinstance(clip, dict):
        raise VideoInputError(f"Vídeo de referência {index} está em formato inválido.")

    url = clip.get("url")
    if not url:
        raise VideoInputError(f"Vídeo de referência {index}: falta a URL.")

    try:
        start = float(clip.get("start", 0))
        ends = float(clip["ends"])
    except (KeyError, TypeError, ValueError) as exc:
        raise VideoInputError(
            f"Vídeo de referência {index}: informe 'start' e 'ends' em segundos."
        ) from exc

    if start < 0:
        raise VideoInputError(f"Vídeo de referência {index}: 'start' não pode ser negativo.")
    if ends <= start:
        raise VideoInputError(f"Vídeo de referência {index}: 'ends' precisa ser maior que 'start'.")
    if ends - start > OMNI_MAX_CLIP_SECONDS:
        raise VideoInputError(
            f"Vídeo de referência {index}: o trecho tem {ends - start:.1f}s. "
            f"O máximo é {OMNI_MAX_CLIP_SECONDS:.0f}s."
        )

    return {"url": str(url), "start": start, "ends": ends}


def build_input(model: str, **kwargs) -> Dict[str, Any]:
    """Dispatch to the builder for `model`."""
    if model == GEMINI_OMNI_FLASH:
        return build_gemini_omni_input(**kwargs)

    raise VideoInputError(
        f"O modelo '{model}' ainda não tem geração implementada. "
        f"Disponível agora: {', '.join(SUPPORTED_MODELS)}."
    )
