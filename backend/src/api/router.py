from fastapi import APIRouter
from src.api.v1 import documents, audits, obligations, relationships


api_router = APIRouter()
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(relationships.router, prefix="/relationships", tags=["relationships"])
api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
api_router.include_router(obligations.router, prefix="/obligations", tags=["obligations"])
