from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.session import get_db_session
from src.database.models import AuditFlag
from src.api.v1.schemas import AuditFlagCreate, AuditFlagResponse, AuditFlagStatusUpdate


router = APIRouter()


@router.post("/", response_model=AuditFlagResponse, status_code=status.HTTP_201_CREATED)
async def create_audit_flag(
    audit_flag: AuditFlagCreate,
    session: AsyncSession = Depends(get_db_session),
):
    db_audit_flag = AuditFlag(**audit_flag.model_dump())
    session.add(db_audit_flag)
    await session.commit()
    await session.refresh(db_audit_flag)
    return db_audit_flag


@router.get("/", response_model=List[AuditFlagResponse])
async def list_audit_flags(
    document_version_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
):
    query = select(AuditFlag)
    if document_version_id:
        query = query.where(AuditFlag.document_version_id == document_version_id)
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    audit_flags = result.scalars().all()
    return audit_flags


@router.get("/{audit_flag_id}", response_model=AuditFlagResponse)
async def get_audit_flag(
    audit_flag_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(AuditFlag).where(AuditFlag.id == audit_flag_id))
    audit_flag = result.scalar_one_or_none()
    if not audit_flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit flag not found")
    return audit_flag


@router.patch("/flags/{flag_id}", response_model=AuditFlagResponse)
async def update_audit_flag(
    flag_id: UUID,
    status_update: AuditFlagStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(AuditFlag).where(AuditFlag.id == flag_id))
    audit_flag = result.scalar_one_or_none()
    if not audit_flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit flag not found")
    
    audit_flag.status = status_update.status
    
    await session.commit()
    await session.refresh(audit_flag)
    return audit_flag
