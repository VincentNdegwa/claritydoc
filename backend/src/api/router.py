from fastapi import APIRouter
from src.api.v1 import documents, audits, obligations, relationships, webhooks


api_router = APIRouter()
api_router.include_router(documents.router, prefix="/v1/documents", tags=["documents"])
api_router.include_router(relationships.router, prefix="/v1/relationships", tags=["relationships"])
api_router.include_router(audits.router, prefix="/v1/audits", tags=["audits"])
api_router.include_router(obligations.router, prefix="/v1/obligations", tags=["obligations"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
