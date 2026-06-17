import httpx

from app.config import Settings


class ElevenLabsTTS:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.elevenlabs_api_key)

    async def synthesize_speech(self, text: str) -> bytes:
        if not self.configured:
            raise RuntimeError("ELEVENLABS_API_KEY is not configured.")

        url = (
            f"https://api.elevenlabs.io/v1/text-to-speech/"
            f"{self.settings.elevenlabs_voice_id}/stream"
        )
        params = {"output_format": self.settings.elevenlabs_output_format}
        payload = {
            "text": text,
            "model_id": self.settings.elevenlabs_model_id,
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.75,
                "style": 0.2,
                "use_speaker_boost": True,
            },
        }
        headers = {
            "xi-api-key": self.settings.elevenlabs_api_key,
            "accept": "audio/mpeg",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params, json=payload, headers=headers)
            response.raise_for_status()
            return response.content
