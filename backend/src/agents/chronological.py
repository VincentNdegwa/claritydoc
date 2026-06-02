import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.services.ai.factory import ai_gateway
from src.services.ai.telemetry import log_inference_metrics
from src.database.models import DocumentChunk, Obligation


class ExtractedCommitment(BaseModel):
    title: str = Field(description="Descriptive name of the timeline tracking target (e.g., Automatic Non-Renewal Window Closure)")
    description: str = Field(description="Detailed overview of the action requirement details")
    iso_due_date: Optional[str] = Field(description="Absolute YYYY-MM-DD date string mapping if explicitly declared, else null")
    trigger_condition: str = Field(description="Textual rule definition (e.g., 30 days prior to annual contract rollover milestone)")
    alert_lead_days: int = Field(default=30, description="Cushion warning window threshold timeline to send reminder notifications")


class ChronoTimelineSchema(BaseModel):
    commitments: List[ExtractedCommitment]


CHRONO_SYSTEM_PROMPT = """
ROLE:
You are an automated timeline extraction engine tracking corporate obligations. Isolate explicit or implied execution deadlines, notice windows, and milestone event conditions.
"""


class ChronologicalAgent:
    async def extract_timeline_commitments(self, db: AsyncSession, user_id: uuid.UUID, document_id: uuid.UUID, version_id: uuid.UUID) -> None:
        query = select(DocumentChunk).where(DocumentChunk.document_version_id == version_id)
        result = await db.execute(query)
        chunks = result.scalars().all()

        for chunk in chunks:
            parsed_schema, tracking_meta = await ai_gateway.generate_structured_output(
                system_prompt=CHRONO_SYSTEM_PROMPT,
                user_content=chunk.raw_text,
                response_model=ChronoTimelineSchema
            )
            
            await log_inference_metrics(db, user_id, document_id, "ChronologicalAgent", tracking_meta)
            
            for commitment in parsed_schema.commitments:
                parsed_date = None
                if commitment.iso_due_date:
                    try:
                        parsed_date = datetime.strptime(commitment.iso_due_date, "%Y-%m-%d").date()
                    except ValueError:
                        parsed_date = None
                
                obligation = Obligation(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    document_chunk_id=chunk.id,
                    title=commitment.title,
                    description=commitment.description,
                    due_date=parsed_date,
                    trigger_condition=commitment.trigger_condition,
                    alert_lead_days=commitment.alert_lead_days,
                    status="pending"
                )
                db.add(obligation)
                
        await db.commit()


obligation_extractor = ChronologicalAgent()
