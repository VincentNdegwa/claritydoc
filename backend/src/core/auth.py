from typing import Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from clerk_backend_api.security.types import RequestState
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.config import settings
from src.database.session import get_db_session
from src.database.models import User


http_bearer = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    id: UUID
    email: str
    clerk_id: str


def require_auth(
    request: Request,
    _creds: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)] = None,
) -> RequestState:
    state = authenticate_request(
        request,
        AuthenticateRequestOptions(
            secret_key=settings.CLERK_SECRET_KEY,
            jwt_key=settings.CLERK_JWT_KEY,
            authorized_parties=settings.CLERK_AUTHORIZED_PARTIES,
            accepts_token=["session_token"],
        ),
    )
    if not state.is_signed_in:
        raise HTTPException(
            status_code=401,
            detail=state.reason or "unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return state


async def get_current_user(
    state: Annotated[RequestState, Depends(require_auth)],
    db: AsyncSession = Depends(get_db_session),
) -> AuthenticatedUser:
    clerk_id = state.payload["sub"]
    
    query = select(User).where(User.clerk_id == clerk_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            clerk_id=clerk_id,
            email=state.payload.get("email", ""),
            first_name=state.payload.get("first_name"),
            last_name=state.payload.get("last_name"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return AuthenticatedUser(
        id=user.id,
        email=user.email,
        clerk_id=user.clerk_id
    )
