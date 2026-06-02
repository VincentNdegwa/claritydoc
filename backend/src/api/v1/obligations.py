from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.session import get_db_session
from src.database.models import Obligation
from src.api.v1.schemas import ObligationCreate, ObligationResponse, ObligationStatusUpdate


router = APIRouter()


@router.post("/", response_model=ObligationResponse, status_code=status.HTTP_201_CREATED)
async def create_obligation(
    obligation: ObligationCreate,
    session: AsyncSession = Depends(get_db_session),
):
    db_obligation = Obligation(**obligation.model_dump())
    session.add(db_obligation)
    await session.commit()
    await session.refresh(db_obligation)
    return db_obligation


@router.get("/", response_model=List[ObligationResponse])
async def list_obligations(
    document_id: UUID | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
):
    query = select(Obligation)
    if document_id:
        query = query.where(Obligation.document_id == document_id)
    if status:
        query = query.where(Obligation.status == status)
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    obligations = result.scalars().all()
    return obligations


@router.get("/{obligation_id}", response_model=ObligationResponse)
async def get_obligation(
    obligation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(Obligation).where(Obligation.id == obligation_id))
    obligation = result.scalar_one_or_none()
    if not obligation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obligation not found")
    return obligation


@router.patch("/{obligation_id}", response_model=ObligationResponse)
async def update_obligation(
    obligation_id: UUID,
    status_update: ObligationStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(Obligation).where(Obligation.id == obligation_id))
    obligation = result.scalar_one_or_none()
    if not obligation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obligation not found")
    
    obligation.status = status_update.status
    
    await session.commit()
    await session.refresh(obligation)
    return obligation
