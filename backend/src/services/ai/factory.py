from src.config import settings
from src.services.ai.providers.openai_provider import OpenAIProvider


def get_ai_gateway():
    provider_choice = settings.AI_PROVIDER.lower()
    if provider_choice == "openai":
        return OpenAIProvider()
    else:
        raise ValueError(f"Unsupported operational AI provider configuration: {provider_choice}")


ai_gateway = get_ai_gateway()
