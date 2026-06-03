import uuid
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import AsyncSessionFactory
from src.database.models import Document, DocumentVersion, BackgroundJob
from src.agents.parser import document_parser
from src.agents.profiler import document_profiler
from src.agents.auditor import document_auditor
from src.agents.chronological import obligation_extractor


async def execute_pipeline_lifecycle(
    ctx,
    document_id: uuid.UUID,
    version_id: uuid.UUID,
    storage_path: str,
    user_id: uuid.UUID
) -> None:
    logger.info(f"Starting analysis lifecycle execution for document version: {version_id}")
    
    async with AsyncSessionFactory() as db:
        try:
            job = BackgroundJob(
                document_id=document_id,
                task_name="execute_pipeline_lifecycle",
                status="processing",
                started_at=datetime.utcnow()
            )
            db.add(job)
            await db.flush()

            logger.info(f"Stage 1/4: Launching Parser Agent for path: {storage_path}")
            parsed_text = await document_parser.extract_text_content(storage_path)
            
            await _update_version_text(db, version_id, parsed_text)

            logger.info(f"Stage 2/4: Launching Profiler Agent for document: {document_id}")
            profile_metadata = await document_profiler.classify_and_profile(db, user_id, document_id, parsed_text)
            
            await _update_document_profile(
                db=db,
                document_id=document_id,
                title=profile_metadata.get("suggested_title"),
                doc_type=profile_metadata.get("detected_type")
            )

            logger.info(f"Stage 3/4: Launching Auditor Agent for version: {version_id}")
            await document_auditor.execute_audit(
                db=db,
                user_id=user_id,
                document_id=document_id,
                version_id=version_id,
                raw_text=parsed_text,
                doc_type=profile_metadata.get("detected_type")
            )

            logger.info(f"Stage 4/4: Launching Chronological Agent for document: {document_id}")
            await obligation_extractor.extract_timeline_commitments(
                db=db,
                user_id=user_id,
                document_id=document_id,
                version_id=version_id
            )

            await _update_document_status(db, document_id, "analyzed")
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            await db.commit()
            logger.info(f"Pipeline lifecycle completed cleanly for document: {document_id}")

        except Exception as pipeline_error:
            logger.error(f"Critical execution fault on processing pipeline: {pipeline_error}")
            await db.rollback()
            
            await _update_document_status(db, document_id, "error")
            await db.commit()
            logger.error(f"Job failed for document: {document_id}")
            raise pipeline_error


async def _update_version_text(db: AsyncSession, version_id: uuid.UUID, text: str) -> None:
    version = await db.get(DocumentVersion, version_id)
    if version:
        version.parsed_markdown = text

async def _update_document_profile(db: AsyncSession, document_id: uuid.UUID, title: str, doc_type: str) -> None:
    document = await db.get(Document, document_id)
    if document:
        if title:
            document.title = title
        if doc_type:
            document.document_type = doc_type

async def _update_document_status(db: AsyncSession, document_id: uuid.UUID, status_str: str) -> None:
    document = await db.get(Document, document_id)
    if document:
        document.status = status_str
        await db.flush()


class WorkerSettings:
    functions = [execute_pipeline_lifecycle]
    on_startup = None
    on_shutdown = None
    retry_jobs = True
    max_tries = 3
