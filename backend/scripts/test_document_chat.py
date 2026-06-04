import argparse
import asyncio
import uuid

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.api.v1.schemas import DocumentChatRequest
from src.database.models import Document
from src.database.session import AsyncSessionFactory
from src.services.ai.document_chat import generate_document_chat_answer


async def _run_chat(document_id: uuid.UUID, question: str, flag_ids, obligation_ids, chunk_ids):
    async with AsyncSessionFactory() as session:
        document_query = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.current_version))
        )
        document_result = await session.execute(document_query)
        document = document_result.scalar_one_or_none()

        if not document:
            raise SystemExit(f"Document {document_id} not found")

        if not document.current_version:
            raise SystemExit("Document has no active version; run the analysis pipeline first")

        payload = DocumentChatRequest(
            question=question,
            flag_ids=flag_ids,
            obligation_ids=obligation_ids,
            chunk_ids=chunk_ids,
        )

        answer = await generate_document_chat_answer(
            session,
            user_id=document.user_id,
            document=document,
            active_version=document.current_version,
            payload=payload,
        )

        print("=== AI Chat Response ===")
        print(answer)


def _parse_uuid_list(raw_values: list[str] | None):
    if not raw_values:
        return []
    return [uuid.UUID(value) for value in raw_values]


def main():
    parser = argparse.ArgumentParser(description="Invoke the document chat AI helper without hitting the HTTP API")
    parser.add_argument("--document-id", required=True, type=uuid.UUID, help="Document UUID to query")
    parser.add_argument("--question", required=True, help="Question to ask about the document")
    parser.add_argument("--flag-id", action="append", dest="flag_ids", help="Audit flag UUID to include (repeatable)")
    parser.add_argument(
        "--obligation-id", action="append", dest="obligation_ids", help="Obligation UUID to include (repeatable)"
    )
    parser.add_argument("--chunk-id", action="append", dest="chunk_ids", help="Chunk UUID to include (repeatable)")

    args = parser.parse_args()

    asyncio.run(
        _run_chat(
            document_id=args.document_id,
            question=args.question,
            flag_ids=_parse_uuid_list(args.flag_ids),
            obligation_ids=_parse_uuid_list(args.obligation_ids),
            chunk_ids=_parse_uuid_list(args.chunk_ids),
        )
    )


if __name__ == "__main__":
    main()
