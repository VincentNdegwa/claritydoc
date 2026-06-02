import time
from typing import Type, Tuple
from openai import AsyncOpenAI
from src.services.ai.base import AIServiceInterface, T
from src.config import settings


class OpenAIProvider(AIServiceInterface):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.AI_API_KEY)
        self.model_name = settings.AI_MODEL

    async def generate_structured_output(
        self, system_prompt: str, user_content: str, response_model: Type[T], temperature: float = 0.0
    ) -> Tuple[T, dict]:
        start_time = time.perf_counter()
        
        response = await self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=temperature,
            response_format=response_model
        )
        
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        usage = response.usage
        
        metadata = {
            "provider": settings.AI_PROVIDER,
            "model_name": self.model_name,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "cached_tokens": getattr(usage.prompt_tokens_details, "cached_tokens", 0) if hasattr(usage, "prompt_tokens_details") else 0,
            "latency_ms": latency_ms,
            "status_code": "success"
        }
        
        return response.choices[0].message.parsed, metadata
