from openai import AsyncOpenAI

from app.core.config import Settings
from app.dto.extraction import ExtractionResult


class OpenRouterClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def is_configured(self) -> bool:
        return self._settings.extractor.is_configured()

    async def complete_json(self, system_prompt: str, user_prompt: str) -> ExtractionResult:
        client = AsyncOpenAI(
            api_key=self._settings.extractor.OPENROUTER_API_KEY.get_secret_value(),  # type: ignore[union-attr]
            base_url=self._settings.extractor.OPENROUTER_BASE_URL,
        )
        completion = await client.chat.completions.create(
            model=self._settings.extractor.OPENROUTER_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        choice = completion.choices[0]
        usage = completion.usage
        return ExtractionResult(
            content=choice.message.content or "",
            model=completion.model,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
        )
