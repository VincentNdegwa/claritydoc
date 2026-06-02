import uuid
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.ai.factory import ai_gateway
from src.services.ai.telemetry import log_inference_metrics


class ProfileOutputSchema(BaseModel):
    detected_type: str = Field(description="Dynamic legal contract classification tag (e.g., NDA, MSA, SOW, SLA)")
    suggested_title: str = Field(description="Clean, human-readable file title identifying executing organizations")


PROFILER_SYSTEM_PROMPT = """
ROLE:
You are an expert systems profiling automaton tracking corporate document catalog architectures.
OBJECTIVE:
Isolate executive parties, entity names, and functional operational parameters from the raw contract preamble context.
"""


class ProfilerAgent:
    async def classify_and_profile(self, db: AsyncSession, user_id: uuid.UUID, document_id: uuid.UUID, raw_text: str) -> dict:
        preamble_slice = raw_text[:4000]
        
        parsed_schema, tracking_meta = await ai_gateway.generate_structured_output(
            system_prompt=PROFILER_SYSTEM_PROMPT,
            user_content=preamble_slice,
            response_model=ProfileOutputSchema
        )
        
        await log_inference_metrics(db, user_id, document_id, "ProfilerAgent", tracking_meta)
        return parsed_schema.model_dump()


document_profiler = ProfilerAgent()
