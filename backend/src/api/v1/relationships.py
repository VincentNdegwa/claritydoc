from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.session import get_db_session
from src.database.models import DocumentRelationship
from src.core.auth import get_current_user, AuthenticatedUser
from src.api.v1.schemas import DocumentRelationshipCreate, DocumentRelationshipSuccessResponse


router = APIRouter()


@router.post("", response_model=DocumentRelationshipSuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_document_relationship(
    relationship: DocumentRelationshipCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    db_relationship = DocumentRelationship(**relationship.model_dump())
    session.add(db_relationship)
    await session.commit()
    await session.refresh(db_relationship)
    
    return DocumentRelationshipSuccessResponse(
        id=db_relationship.id,
        status="linked"
    )
