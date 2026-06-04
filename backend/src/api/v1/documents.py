import uuid
from collections import defaultdict
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.database.session import get_db_session
from src.database.models import Document, DocumentVersion, DocumentChunk, AuditFlag, Obligation
from src.core.auth import get_current_user, AuthenticatedUser
from src.services.storage import storage_service
from src.agents.pipeline import agent_orchestrator
from src.api.v1.schemas import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentVersionSummary,
    DocumentFlagSummary,
    DeepAnalysisViewResponse,
    DocumentVersionResponse,
    AuditFlagResponse,
    DocumentChunkPreviewResponse,
    ObligationPreviewResponse,
)

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    file_extension = f".{file.filename.split('.')[-1].lower()}" if "." in file.filename else ""
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{file_extension}'. Only PDF and DOCX documents are accepted."
        )

    document_id = uuid.uuid4()
    version_id = uuid.uuid4()
    storage_path = f"uploads/{current_user.id}/{document_id}/{version_id}{file_extension}"

    try:
        await storage_service.upload_file(file_object=file.file, target_path=storage_path)
    except Exception as upload_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File ingestion layer execution fault: {str(upload_err)}"
        )

    new_document = Document(
        id=document_id,
        user_id=current_user.id,
        title=file.filename,
        document_type=document_type,
        status="processing",
        current_version_id=None,
    )
    db.add(new_document)
    await db.flush()

    initial_version = DocumentVersion(
        id=version_id,
        document_id=document_id,
        version_number=1,
        storage_path=storage_path,
        file_type=file_extension.lstrip("."),
        is_signed=False,
    )
    db.add(initial_version)
    await db.flush()

    new_document.current_version_id = version_id
    await db.flush()
    await db.refresh(new_document)

    await agent_orchestrator.trigger_analysis_pipeline(
        document_id=document_id,
        version_id=version_id,
        storage_path=storage_path,
        user_id=current_user.id
    )

    return new_document


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    query = (
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_details(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    document_query = (
        select(Document)
        .where(Document.id == document_id, Document.user_id == current_user.id)
        .options(selectinload(Document.versions))
    )
    result = await db.execute(document_query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested document resource could not be found or access permissions are invalid."
        )

    versions = sorted(document.versions, key=lambda v: v.version_number, reverse=True)
    version_ids = [version.id for version in versions]

    flag_summary = DocumentFlagSummary(total=0, unresolved=0, resolved=0, by_risk_level={})
    version_flag_counts = {version_id: 0 for version_id in version_ids}

    if version_ids:
        flag_rows = await db.execute(
            select(
                AuditFlag.document_version_id,
                AuditFlag.risk_level,
                AuditFlag.status,
                func.count(AuditFlag.id)
            ).where(AuditFlag.document_version_id.in_(version_ids))
            .group_by(AuditFlag.document_version_id, AuditFlag.risk_level, AuditFlag.status)
        )

        risk_level_totals = defaultdict(int)

        for version_id, risk_level, status_value, count in flag_rows:
            version_flag_counts[version_id] = version_flag_counts.get(version_id, 0) + count
            flag_summary.total += count
            if status_value == "resolved":
                flag_summary.resolved += count
            else:
                flag_summary.unresolved += count
            risk_level_totals[risk_level] += count

        flag_summary.by_risk_level = dict(risk_level_totals)

    version_summaries = [
        DocumentVersionSummary(
            id=version.id,
            version_number=version.version_number,
            created_at=version.created_at,
            storage_path=version.storage_path,
            file_type=version.file_type,
            is_signed=version.is_signed,
            flag_count=version_flag_counts.get(version.id, 0)
        )
        for version in versions
    ]

    return DocumentDetailResponse(
        document=DocumentResponse.model_validate(document),
        versions=version_summaries,
        flag_summary=flag_summary,
    )


@router.get("/{document_id}/analysis", response_model=DeepAnalysisViewResponse)
async def get_document_deep_analysis(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    document_query = (
        select(Document)
        .where(Document.id == document_id, Document.user_id == current_user.id)
        .options(selectinload(Document.current_version))
    )
    document_result = await db.execute(document_query)
    document = document_result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested document aggregate analysis payload could not be found."
        )

    active_version = document.current_version
    if not active_version:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The active target operational layer is detached or missing a reference version model."
        )

    flags_query = (
        select(AuditFlag)
        .where(AuditFlag.document_version_id == active_version.id)
        .order_by(AuditFlag.created_at.desc())
    )
    flags_result = await db.execute(flags_query)

    flag_summary_rows = await db.execute(
        select(
            AuditFlag.risk_level,
            AuditFlag.status,
            func.count(AuditFlag.id)
        )
        .where(AuditFlag.document_version_id == active_version.id)
        .group_by(AuditFlag.risk_level, AuditFlag.status)
    )

    flag_summary = DocumentFlagSummary(total=0, unresolved=0, resolved=0, by_risk_level={})
    flag_risk_totals = defaultdict(int)
    for risk_level, status_value, count in flag_summary_rows:
        flag_summary.total += count
        if status_value == "resolved":
            flag_summary.resolved += count
        else:
            flag_summary.unresolved += count
        flag_risk_totals[risk_level] += count
    flag_summary.by_risk_level = dict(flag_risk_totals)

    chunk_count_result = await db.execute(
        select(func.count(DocumentChunk.id)).where(DocumentChunk.document_version_id == active_version.id)
    )
    chunk_count = chunk_count_result.scalar_one()

    chunk_preview_query = (
        select(DocumentChunk)
        .where(DocumentChunk.document_version_id == active_version.id)
        .order_by(DocumentChunk.chunk_index.asc())
        .limit(10)
    )
    chunk_preview_result = await db.execute(chunk_preview_query)
    chunk_preview = [
        DocumentChunkPreviewResponse(
            id=chunk.id,
            chunk_index=chunk.chunk_index,
            heading=chunk.heading,
            page_number=chunk.page_number,
            preview_text=(chunk.raw_text[:500] + "...") if len(chunk.raw_text) > 500 else chunk.raw_text,
        )
        for chunk in chunk_preview_result.scalars().all()
    ]

    obligations_query = (
        select(Obligation)
        .where(Obligation.document_id == document.id)
        .order_by(Obligation.due_date.asc().nulls_last())
        .limit(20)
    )
    obligations_result = await db.execute(obligations_query)

    obligation_count_result = await db.execute(
        select(func.count(Obligation.id)).where(Obligation.document_id == document.id)
    )
    obligation_count = obligation_count_result.scalar_one()

    obligation_preview = [
        ObligationPreviewResponse(
            id=obligation.id,
            title=obligation.title,
            description=obligation.description,
            due_date=obligation.due_date,
            status=obligation.status,
            document_chunk_id=obligation.document_chunk_id,
        )
        for obligation in obligations_result.scalars().all()
    ]

    return DeepAnalysisViewResponse(
        document=DocumentResponse.model_validate(document),
        active_version=DocumentVersionResponse.model_validate(active_version),
        flag_summary=flag_summary,
        flags=[AuditFlagResponse.model_validate(f) for f in flags_result.scalars().all()],
        chunk_count=chunk_count,
        chunk_preview=chunk_preview,
        obligation_count=obligation_count,
        obligations=obligation_preview,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    from sqlalchemy import delete as sql_delete
    from src.database.models import DocumentChunk, DocumentVersion

    document_query = (
        select(Document)
        .where(Document.id == document_id, Document.user_id == current_user.id)
        .options(selectinload(Document.versions))
    )
    result = await db.execute(document_query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target document eviction resource target could not be found."
        )

    file_paths_to_evict = [version.storage_path for version in document.versions]

    await db.execute(
        sql_delete(DocumentChunk)
        .where(DocumentChunk.document_version_id.in_([v.id for v in document.versions]))
    )
    await db.execute(
        sql_delete(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
    )
    await db.execute(
        sql_delete(Document)
        .where(Document.id == document_id)
    )
    await db.commit()

    for path in file_paths_to_evict:
        try:
            await storage_service.delete_file(target_path=path)
        except Exception:
            continue