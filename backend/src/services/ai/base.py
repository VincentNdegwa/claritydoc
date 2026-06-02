from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Type, TypeVar, Tuple

T = TypeVar('T', bound=BaseModel)


class AIServiceInterface(ABC):
    @abstractmethod
    async def generate_structured_output(
        self, 
        system_prompt: str, 
        user_content: str, 
        response_model: Type[T],
        temperature: float = 0.0
    ) -> Tuple[T, dict]:
        """
        Executes inference, forces structured JSON mapping, and returns 
        the parsed schema alongside the raw token accounting metadata.
        """
        pass
