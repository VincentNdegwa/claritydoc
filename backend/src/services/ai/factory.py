from src.config import settings
from src.services.ai.providers.openai_provider import OpenAIProvider
from src.services.ai.providers.mistral_provider import MistralProvider


def get_ai_gateway():
    provider_choice = settings.AI_PROVIDER.lower()
    if provider_choice == "openai":
        return OpenAIProvider()
    elif provider_choice == "mistral":
        return MistralProvider()
    else:
        raise ValueError(f"Unsupported operational AI provider configuration: {provider_choice}")


ai_gateway = get_ai_gateway()
