import json
import logging
from typing import Dict, List, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5"


class MissingCredentialError(RuntimeError):
    """No API key is configured for the active provider."""


class AIAnalyzer:
    """Analyzes video content and provides creative direction using Claude."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        if not api_key:
            raise MissingCredentialError(
                "Nenhuma chave de API configurada. Abra a tela de Integrações "
                "e cadastre uma chave antes de analisar vídeos."
            )
        self.client = Anthropic(api_key=api_key)
        self.model = model or DEFAULT_MODEL

    @classmethod
    def from_configuration(cls) -> "AIAnalyzer":
        """
        Build an analyzer from the credential vault / environment, using the
        provider and model selected in the Integrações screen.
        """
        # Imported here to keep this module importable without the API layer.
        from app.services.preferences import load_preferences
        from app.services.providers import resolve_key

        prefs = load_preferences()
        provider_id = prefs.get("active_provider") or "anthropic"
        model = prefs.get("active_model") if provider_id == "anthropic" else None

        api_key, source = resolve_key(provider_id)
        if not api_key:
            raise MissingCredentialError(
                f"Nenhuma chave configurada para o provedor '{provider_id}'. "
                "Cadastre uma na tela de Integrações."
            )

        if provider_id != "anthropic":
            # Non-Anthropic providers are catalogued and testable today; the
            # analysis client itself still speaks the Anthropic API.
            raise MissingCredentialError(
                f"O provedor '{provider_id}' ainda não é suportado pela análise "
                "criativa. Selecione um modelo Claude na tela de Integrações."
            )

        logger.info("AIAnalyzer using provider=%s model=%s (key from %s)",
                    provider_id, model or DEFAULT_MODEL, source)
        return cls(api_key=api_key, model=model)

    async def analyze_emotional_vibe(
        self, vibe_description: str, video_metadata: Dict
    ) -> Dict:
        """Analyzes the emotional intent and provides creative direction."""

        prompt = f"""
        You are a premium video editor and creative director analyzing content for Instagram Reels/TikTok.

        VIDEO METADATA:
        - Duration: {video_metadata.get('duration', 'Unknown')}s
        - Has speech: {video_metadata.get('has_speech', False)}
        - Visual style hints: {video_metadata.get('visual_hints', [])}

        EMOTIONAL VIBE REQUESTED: {vibe_description}

        Analyze and provide creative direction in JSON format with these fields:
        {{
            "primary_emotion": "main emotion to convey",
            "secondary_emotions": ["supporting emotions"],
            "intensity": 0.0-1.0,
            "recommended_pacing": "fast/medium/slow/dynamic",
            "color_temperature": "warm/cool/neutral/vibrant",
            "suggested_music_mood": "description of music style",
            "cut_rhythm": "beats per minute and cutting style",
            "visual_density": "minimal/moderate/intense",
            "typography_style": "minimalist/bold/elegant/playful",
            "transition_style": "smooth/sharp/dynamic/seamless",
            "camera_movement": "static/subtle/dynamic/aggressive",
            "suggested_effects": ["list of recommended effects"],
            "color_grading": {{
                "tone": "description",
                "saturation": "low/medium/high",
                "contrast": "low/medium/high",
                "highlights": "specific color adjustments"
            }},
            "hook_suggestion": "how to start strong",
            "retention_strategy": "how to keep viewers engaged"
        }}

        Be specific and actionable. This data will drive automated video editing decisions.
        """

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            analysis = json.loads(response.content[0].text)
            return analysis
        except json.JSONDecodeError:
            logger.error("Failed to parse Claude response as JSON")
            return self._default_analysis()

    async def suggest_aesthetic_style(
        self, references: List[str], vibe: str
    ) -> Dict:
        """Suggests visual aesthetic based on references and vibe."""

        refs_str = "\n".join(references)

        prompt = f"""
        Based on these reference descriptions and emotional vibe, suggest a specific visual aesthetic.

        REFERENCES:
        {refs_str}

        VIBE: {vibe}

        Suggest in JSON:
        {{
            "aesthetic_name": "e.g., luxury editorial, clean minimal, dark luxury",
            "visual_elements": ["key visual characteristics"],
            "color_palette": ["hex colors"],
            "typography": "font style recommendations",
            "motion_style": "how elements should move",
            "texture": "texture to apply if any",
            "inspiration_era": "what era/style period"
        }}
        """

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            aesthetic = json.loads(response.content[0].text)
            return aesthetic
        except json.JSONDecodeError:
            logger.error("Failed to parse aesthetic suggestion")
            return {}

    async def analyze_script_and_tone(self, script: str) -> Dict:
        """Analyzes script tone, emphasis points, and emotional beats."""

        prompt = f"""
        Analyze this video script for emotional beats, emphasis points, and pacing.

        SCRIPT:
        {script}

        Provide analysis in JSON:
        {{
            "emotional_beats": [
                {{"timestamp": "0:00-0:05", "emotion": "energy", "intensity": 0.8, "suggested_cut": true}}
            ],
            "emphasis_points": ["key phrases that need visual focus"],
            "natural_pauses": ["where to cut for rhythm"],
            "voice_tone_suggestions": {{"pace": "fast/normal/slow", "energy": 0-1}},
            "pacing_rhythm": "suggested BPM for cuts",
            "hook_potential": "0.0-1.0 engagement prediction"
        }}
        """

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            analysis = json.loads(response.content[0].text)
            return analysis
        except json.JSONDecodeError:
            logger.error("Failed to parse script analysis")
            return {}

    def _default_analysis(self) -> Dict:
        """Returns default analysis structure."""
        return {
            "primary_emotion": "engagement",
            "secondary_emotions": ["interest"],
            "intensity": 0.7,
            "recommended_pacing": "dynamic",
            "color_temperature": "vibrant",
            "suggested_music_mood": "energetic",
            "cut_rhythm": "120 BPM",
            "visual_density": "moderate",
            "typography_style": "clean minimal",
            "transition_style": "smooth",
            "camera_movement": "subtle",
            "suggested_effects": [],
            "color_grading": {
                "tone": "vibrant",
                "saturation": "medium",
                "contrast": "medium",
            },
        }
