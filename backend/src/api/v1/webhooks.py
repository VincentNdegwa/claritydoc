from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from svix.webhooks import Webhook, WebhookVerificationError
from src.config import settings
from src.database.session import get_db_session
from src.database.models import User


router = APIRouter()


@router.post("/clerk")
async def clerk_webhook(request: Request, db: AsyncSession = Depends(get_db_session)):
    """
    Handles Clerk webhook events to sync user data.
    
    Events handled:
    - user.created: Creates a new user in our database
    - user.updated: Updates existing user data
    - user.deleted: Deletes user from our database
    """
    body = await request.body()
    headers = dict(request.headers)
    
    try:
        event = Webhook(settings.CLERK_WEBHOOK_SIGNING_SECRET).verify(body, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    event_type = event["type"]
    data = event["data"]
    
    if event_type == "user.created":
        await handle_user_created(data, db)
    elif event_type == "user.updated":
        await handle_user_updated(data, db)
    elif event_type == "user.deleted":
        await handle_user_deleted(data["id"], db)
    
    return {"ok": True}


async def handle_user_created(data: dict, db: AsyncSession):
    """Create a new user from Clerk webhook data."""
    clerk_id = data["id"]
    
    # Check if user already exists (idempotent)
    query = select(User).where(User.clerk_id == clerk_id)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return  # Already exists, skip
    
    # Extract email
    email = None
    for address in data.get("email_addresses") or []:
        if address["id"] == data.get("primary_email_address_id"):
            email = address["email_address"]
            break
    
    # Extract name from primary phone or first_name/last_name
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    
    user = User(
        clerk_id=clerk_id,
        email=email or "",
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    await db.commit()


async def handle_user_updated(data: dict, db: AsyncSession):
    """Update existing user from Clerk webhook data."""
    clerk_id = data["id"]
    
    query = select(User).where(User.clerk_id == clerk_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # User doesn't exist, create it
        await handle_user_created(data, db)
        return
    
    # Extract email
    email = None
    for address in data.get("email_addresses") or []:
        if address["id"] == data.get("primary_email_address_id"):
            email = address["email_address"]
            break
    
    # Update fields
    if email:
        user.email = email
    user.first_name = data.get("first_name")
    user.last_name = data.get("last_name")
    
    await db.commit()


async def handle_user_deleted(clerk_id: str, db: AsyncSession):
    """Delete user from our database."""
    query = select(User).where(User.clerk_id == clerk_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user:
        await db.delete(user)
        await db.commit()
