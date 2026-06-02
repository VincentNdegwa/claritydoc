import uuid
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.services.ai.factory import ai_gateway
from src.services.ai.telemetry import log_inference_metrics
from src.database.models import DocumentChunk, AuditFlag


class SingleRiskFinding(BaseModel):
    category: str = Field(description="Specific legal risk type (e.g., ip_ownership, liability_cap, asymmetrical_termination)")
    risk_level: str = Field(description="Must match exact value constraints: low, medium, high, critical")
    issue_summary: str = Field(description="Concise description mapping the localized contract issue")
    detailed_explanation: str = Field(description="Plain English summary highlighting the operational risk exposure to the user")
    playbook_counter_proposal: str = Field(description="Strategic alternative text proposals or counter-scripts for negotiation")


class AuditResultSchema(BaseModel):
    findings: List[SingleRiskFinding]


AUDITOR_SYSTEM_PROMPT = """
ROLE:
You are an elite corporate legal risk validator. Scan the provided section of text for asymmetric liabilities, indemnification loops, or hidden commercial traps.
CRITICAL CONSTRAINT:
If zero verified high risks are present in the text, you MUST return an empty array. Do not generate generic commentary.
"""


class AuditorAgent:
    async def execute_audit(self, db: AsyncSession, user_id: uuid.UUID, document_id: uuid.UUID, version_id: uuid.UUID, raw_text: str, doc_type: str) -> None:
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
        chunk_records = []
        
        for index, text in enumerate(paragraphs):
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_version_id=version_id,
                chunk_index=index,
                raw_text=text
            )
            db.add(chunk)
            chunk_records.append(chunk)
            
        await db.flush()

        for chunk in chunk_records:
            parsed_schema, tracking_meta = await ai_gateway.generate_structured_output(
                system_prompt=AUDITOR_SYSTEM_PROMPT + f"\nContext baseline schema target document format: {doc_type}",
                user_content=chunk.raw_text,
                response_model=AuditResultSchema
            )
            
            await log_inference_metrics(db, user_id, document_id, "AuditorAgent", tracking_meta)
            
            for finding in parsed_schema.findings:
                flag = AuditFlag(
                    id=uuid.uuid4(),
                    document_version_id=version_id,
                    document_chunk_id=chunk.id,
                    risk_level=finding.risk_level,
                    category=finding.category,
                    issue_summary=finding.issue_summary,
                    detailed_explanation=finding.detailed_explanation,
                    playbook_counter_proposal=finding.playbook_counter_proposal,
                    status="unresolved"
                )
                db.add(flag)
                
        await db.commit()


document_auditor = AuditorAgent()
