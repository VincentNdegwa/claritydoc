import uuid
from typing import List, Literal
from loguru import logger
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.services.ai.factory import ai_gateway
from src.services.ai.telemetry import log_inference_metrics
from src.database.models import DocumentChunk, AuditFlag


class SingleRiskFinding(BaseModel):
    category: str = Field(
        description="Specific legal risk type (e.g., ip_ownership, liability_cap, asymmetrical_termination)",
        min_length=1,
        max_length=100,
    )
    risk_level: Literal["low", "medium", "high", "critical"] = Field(
        description="Must match exact value constraints: low, medium, high, critical"
    )
    issue_summary: str = Field(
        description="Concise description mapping the localized contract issue",
        min_length=1,
        max_length=255,
    )
    detailed_explanation: str = Field(
        description="Plain English summary highlighting the operational risk exposure to the user",
        min_length=1,
        max_length=4000,
    )
    playbook_counter_proposal: str = Field(
        description="Strategic alternative text proposals or counter-scripts for negotiation",
        min_length=1,
        max_length=2000,
    )


class AuditResultSchema(BaseModel):
    findings: List[SingleRiskFinding]


AUDITOR_SYSTEM_PROMPT = """
ROLE:
You are an elite corporate legal risk validator. Scan the provided section of text for asymmetric liabilities, indemnification loops, or hidden commercial traps.
CRITICAL CONSTRAINT:
If zero substantiated risks of any severity are present in the text, return an empty array. Otherwise enumerate every clause that creates a material exposure and assign the appropriate risk_level (low, medium, high, critical) based on likelihood and impact. Do not suppress medium or low risks.
All string fields must respect their maximum lengths: category (100 chars), issue_summary (255 chars), detailed_explanation (4000 chars), playbook_counter_proposal (2000 chars).

FACTUALITY RULES:
1. Only describe a risk if the provided text explicitly contains the supporting clause. Quote or paraphrase the exact contract language in the detailed_explanation.
2. Every finding must reference the specific section heading or paragraph label that triggered the concern (e.g., "Section 4.A" or "Insurance clause, page 5"). If no heading is supplied, describe the relevant clause in plain language (e.g., "Data sharing paragraph").
3. If the text already provides a reciprocal protection that mitigates the risk, either skip the finding or explicitly explain why that protection is insufficient.
4. Never speculate about obligations, indemnities, or payments that are not stated verbatim in the text. If evidence is incomplete, return an empty findings list for that chunk.
"""


class AuditorAgent:
    async def execute_audit(self, db: AsyncSession, user_id: uuid.UUID, document_id: uuid.UUID, version_id: uuid.UUID, raw_text: str, doc_type: str) -> None:
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
        chunk_records = []
        char_position = 0
        
        for index, text in enumerate(paragraphs):
            char_start = raw_text.find(text, char_position)
            char_end = char_start + len(text) if char_start >= 0 else char_position + len(text)
            
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_version_id=version_id,
                chunk_index=index,
                raw_text=text,
                char_start=char_start,
                char_end=char_end
            )
            db.add(chunk)
            chunk_records.append(chunk)
            char_position = char_end
            
        await db.flush()

        for chunk in chunk_records:
            try:
                parsed_schema, tracking_meta = await ai_gateway.generate_structured_output(
                    system_prompt=AUDITOR_SYSTEM_PROMPT + f"\nContext baseline schema target document format: {doc_type}",
                    user_content=chunk.raw_text,
                    response_model=AuditResultSchema
                )
            except ValidationError as validation_err:
                logger.error(
                    "AuditorAgent structured output failed for document={} chunk_index={} version={} error={} input_preview={}",
                    document_id,
                    chunk.chunk_index,
                    version_id,
                    validation_err,
                    getattr(validation_err, "errors", lambda: [])()
                )
                raise
            
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
