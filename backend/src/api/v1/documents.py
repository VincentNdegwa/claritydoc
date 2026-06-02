import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.database.session import get_db_session
from src.database.models import Document, DocumentVersion, DocumentChunk, AuditFlag
from src.core.auth import auth_validator, AuthenticatedUser
from src.services.storage import storage_service
from src.agents.pipeline import agent_orchestrator
from src.api.v1.schemas import (
    DocumentResponse,
    DeepAnalysisViewResponse,
    DocumentVersionResponse,
    AuditFlagResponse,
    DocumentChunkResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(auth_validator.validate_token),
):
    """
    Ingests an incoming raw legal document file, writes it to persistent cloud object storage,
    registers database ledger records, and triggers the asynchronous multi-agent evaluation lifecycle.
    """
    # 1. Basic Content Validation
    allowed_extensions = {".pdf", ".docx"}
    file_extension = f".{file.filename.split('.')[-1].lower()}" if "." in file.filename else ""
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{file_extension}'. Only PDF and DOCX documents are accepted."
        )

    # 2. Allocate Structural Primary Identifiers
    document_id = uuid.uuid4()
    version_id = uuid.uuid4()
    
    # 3. Stream File Data to Cloud Storage Target
    # Path partitioning layout pattern: uploads/{user_id}/{document_id}/{version_id}{ext}
    storage_path = f"uploads/{current_user.id}/{document_id}/{version_id}{file_extension}"
    try:
        await storage_service.upload_file(file_object=file.file, target_path=storage_path)
    except Exception as upload_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File ingestion layer execution fault: {str(upload_err)}"
        )

    # 4. Generate Database Records within Transaction
    new_document = Document(
        id=document_id,
        user_id=current_user.id,
        title=file.filename,
        document_type=document_type,
        status="processing",
        current_version_id=version_id,
    )
    
    initial_version = DocumentVersion(
        id=version_id,
        document_id=document_id,
        version_number=1,
        storage_path=storage_path,
        file_type=file_extension.lstrip("."),
        is_signed=False,
    )
    
    db.add(new_document)
    db.add(initial_version)
    
    # Force flushing to capture data and ensure structural references align
    await db.flush()

    # 5. Hand Off to Background Processing Agents
    # Runs fire-and-forget or task queue orchestration out of band so request resolves fast
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
    current_user: AuthenticatedUser = Depends(auth_validator.validate_token),
):
    """
    Fetches the global document index belonging to the authenticated entity
    ordered chronologically by creation timestamps.
    """
    query = (
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(query)
    documents = result.scalars().all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_details(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(auth_validator.validate_token),
):
    """
    Retrieves isolated structural metadata record information for a single historical document instance.
    """
    query = select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested document resource could not be found or access permissions are invalid."
        )
    return document


@router.get("/{document_id}/analysis", response_model=DeepAnalysisViewResponse)
async def get_document_deep_analysis(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(auth_validator.validate_token),
):
    """
    Compiles a comprehensive graph lookup view for the workspace dashboard.
    Fetches active version string trees, precise bounding index highlights,
    and outstanding risk tags in a unified, eager-loaded relation layout.
    """
    # 1. Eager load the entire target container model along with its structural version child pointer
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

    # 2. Concurrently fetch associated layout chunk strings and audit findings 
    chunks_query = (
        select(DocumentChunk)
        .where(DocumentChunk.document_version_id == active_version.id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    flags_query = (
        select(AuditFlag)
        .where(AuditFlag.document_version_id == active_version.id)
        .order_by(AuditFlag.created_at.desc())
    )

    chunks_result = await db.execute(chunks_query)
    flags_result = await db.execute(flags_query)

    # 3. Assemble and map data to the deep workspace analysis composite schema
    return DeepAnalysisViewResponse(
        document=DocumentResponse.model_validate(document),
        active_version=DocumentVersionResponse.model_validate(active_version),
        flags=[AuditFlagResponse.model_validate(f) for f in flags_result.scalars().all()],
        chunks=[DocumentChunkResponse.model_validate(c) for c in chunks_result.scalars().all()],
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(auth_validator.validate_token),
):
    """
    Enforces cascading resource deletion. Removes relational trace coordinates from local systems 
    and issues an eviction call to cloud object storage paths matching the document version catalog.
    """
    # 1. Verify existence and extract metadata contexts
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

    # 2. Compile storage trajectories for object bucket cleanups
    file_paths_to_evict = [version.storage_path for version in document.versions]

    # 3. Execute cascading ORM records deletion
    # Relational foreign keys configured with ON DELETE CASCADE automatically purge
    # linked document_versions, document_chunks, audit_flags, and obligations.
    await db.delete(document)
    await db.commit()

    # 4. Asynchronously purge binary attachments from cloud object infrastructure
    # Executed after database commit completes successfully to avoid data drift
    for path in file_paths_to_evict:
        try:
            await storage_service.delete_file(target_path=path)
        except Exception as storage_err:
            # Catch internal exception traces silently to guarantee API request completion
            # implement operational background dead-letter logs as necessary
            continue