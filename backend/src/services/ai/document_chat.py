import uuid
from typing import List

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.api.v1.schemas import DocumentChatRequest
from src.database.models import (
    AuditFlag,
    Document,
    DocumentChunk,
    DocumentVersion,
    Obligation,
)
from src.services.ai.factory import ai_gateway
from src.services.ai.telemetry import log_inference_metrics


DOCUMENT_CHAT_SYSTEM_PROMPT = """
ROLE:
You are ClarityDoc's embedded contract analyst. Provide practical, well-structured answers that reference the supplied audit flags, obligations, or raw clause snippets.

INSTRUCTIONS:
1. Only use the provided context; if evidence is missing, clearly state that you cannot find that detail instead of speculating.
2. Always return valid JSON exactly like this example (including escaped newlines):
   {
     "answer": "## Summary\\n- point one\\n\\n### Flag: Example\\nDetails here\\nReference: {flag:11111111-1111-1111-1111-111111111111}"
   }
   Never wrap the entire answer in quotes or code blocks outside the JSON object.
3. Begin every response with a `## Summary` section that highlights the top 2–3 insights in plain language.
4. When referencing an audit flag or obligation, follow this template exactly:
   - Introduce the item with a level-3 heading: `### Flag: <title>` or `### Obligation: <title>` (never include the UUID in the heading).
   - Provide 2–3 short paragraphs covering plain-language description, risks, and recommended actions.
   - Immediately end the section with a plain-text standalone sentence (no bold/italics) that literally matches one of the following:
     - `Reference: {flag:00000000-0000-0000-0000-000000000000}`
     - `Reference: {obligation:00000000-0000-0000-0000-000000000000}`
     Replace the zeros with the exact UUID supplied in context, preserving braces.
5. Keep answers grounded, concise, and action-focused. Prefer bullet lists for steps, but avoid runaway verbosity.
6. Treat each flag or obligation independently: never merge descriptions or IDs across items, and do not invent cross references unless the context explicitly links them.
"""


class DocumentChatAnswerSchema(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)


def _truncate_text(value: str | None, limit: int = 900) -> str:
    if not value:
        return ""
    trimmed = value.strip()
    if len(trimmed) <= limit:
        return trimmed
    return trimmed[:limit].rstrip() + "..."


async def generate_document_chat_answer(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    document: Document,
    active_version: DocumentVersion,
    payload: DocumentChatRequest,
) -> str:
    context_sections = [
        f"Document Title: {document.title}",
        f"Document Type: {document.document_type}",
        f"Document Status: {document.status}",
    ]

    flag_rows = await _load_flag_rows(db, active_version.id, payload.flag_ids)
    for flag_obj, chunk_text in flag_rows:
        context_sections.append(
            (
                f"AUDIT FLAG {flag_obj.id} | risk={flag_obj.risk_level} | category={flag_obj.category}\n"
                f"Summary: {flag_obj.issue_summary}\n"
                f"Details: {_truncate_text(flag_obj.detailed_explanation, 700)}"
            )
        )
        if chunk_text:
            context_sections.append(
                f"Source clause excerpt for flag {flag_obj.id}:\n{_truncate_text(chunk_text, 700)}"
            )

    obligation_rows = await _load_obligation_rows(db, document.id, payload.obligation_ids)
    for obligation_obj, chunk_text in obligation_rows:
        due_text = obligation_obj.due_date.isoformat() if obligation_obj.due_date else "unspecified"
        context_sections.append(
            (
                f"OBLIGATION {obligation_obj.id} | title={obligation_obj.title}\n"
                f"Due: {due_text} | Status: {obligation_obj.status}\n"
                f"Trigger: {_truncate_text(obligation_obj.trigger_condition, 400)}\n"
                f"Description: {_truncate_text(obligation_obj.description, 600)}"
            )
        )
        if chunk_text:
            context_sections.append(
                f"Source clause excerpt for obligation {obligation_obj.id}:\n{_truncate_text(chunk_text, 700)}"
            )

    chunk_rows = await _load_chunk_rows(db, active_version.id, payload.chunk_ids)
    for chunk in chunk_rows:
        context_sections.append(
            f"HIGHLIGHTED CLAUSE {chunk.id} | index={chunk.chunk_index}\n{_truncate_text(chunk.raw_text, 900)}"
        )

    if len(context_sections) == 3:
        context_sections.append(
            "No audit flags, obligations, or clause highlights were found for the selected filters."
        )

    context_blob = "\n\n".join(context_sections)

    user_prompt = (
        "You will receive document context followed by a user question. "
        "Reference IDs when they are available and keep the answer focused on the provided snippets."
    )
    chat_input = f"{user_prompt}\n\nCONTEXT:\n{context_blob}\n\nQUESTION:\n{payload.question.strip()}"

    parsed_schema, tracking_meta = await ai_gateway.generate_structured_output(
        system_prompt=DOCUMENT_CHAT_SYSTEM_PROMPT,
        user_content=chat_input,
        response_model=DocumentChatAnswerSchema,
        temperature=0.2,
    )

    await log_inference_metrics(
        db,
        user_id,
        document.id,
        "DocumentChatEndpoint",
        tracking_meta,
    )

    return parsed_schema.answer


async def _load_flag_rows(
    db: AsyncSession,
    version_id: uuid.UUID,
    requested_flag_ids: List[uuid.UUID],
):
    selected_flag_ids = requested_flag_ids[:10]
    flag_query = (
        select(AuditFlag, DocumentChunk.raw_text.label("chunk_text"))
        .outerjoin(DocumentChunk, AuditFlag.document_chunk_id == DocumentChunk.id)
        .where(AuditFlag.document_version_id == version_id)
    )
    if selected_flag_ids:
        flag_query = flag_query.where(AuditFlag.id.in_(selected_flag_ids))
    else:
        flag_query = flag_query.order_by(AuditFlag.created_at.desc()).limit(3)

    return (await db.execute(flag_query)).all()


async def _load_obligation_rows(
    db: AsyncSession,
    document_id: uuid.UUID,
    requested_obligation_ids: List[uuid.UUID],
):
    selected_obligation_ids = requested_obligation_ids[:10]
    obligation_query = (
        select(Obligation, DocumentChunk.raw_text.label("chunk_text"))
        .outerjoin(DocumentChunk, Obligation.document_chunk_id == DocumentChunk.id)
        .where(Obligation.document_id == document_id)
    )
    if selected_obligation_ids:
        obligation_query = obligation_query.where(Obligation.id.in_(selected_obligation_ids))
    else:
        obligation_query = obligation_query.order_by(Obligation.due_date.asc().nulls_last()).limit(5)

    return (await db.execute(obligation_query)).all()


async def _load_chunk_rows(
    db: AsyncSession,
    version_id: uuid.UUID,
    requested_chunk_ids: List[uuid.UUID],
):
    selected_chunk_ids = requested_chunk_ids[:5]
    if not selected_chunk_ids:
        return []

    chunk_query = (
        select(DocumentChunk)
        .where(
            DocumentChunk.document_version_id == version_id,
            DocumentChunk.id.in_(selected_chunk_ids),
        )
    )
    return (await db.execute(chunk_query)).scalars().all()
