from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    title: str
    document_type: str
    status: str = "draft"


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: str | None = None
    status: str | None = None


class DocumentResponse(DocumentBase):
    id: UUID
    user_id: UUID
    current_version_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentFlagSummary(BaseModel):
    total: int = 0
    unresolved: int = 0
    resolved: int = 0
    by_risk_level: dict[str, int] = Field(default_factory=dict)


class DocumentVersionSummary(BaseModel):
    id: UUID
    version_number: int
    created_at: datetime
    storage_path: str
    file_type: str
    is_signed: bool
    flag_count: int = 0


class DocumentDetailResponse(BaseModel):
    document: DocumentResponse
    versions: list[DocumentVersionSummary]
    flag_summary: DocumentFlagSummary


class DocumentVersionBase(BaseModel):
    version_number: int = 1
    storage_path: str
    file_type: str
    is_signed: bool = False


class DocumentVersionCreate(DocumentVersionBase):
    document_id: UUID


class DocumentVersionResponse(DocumentVersionBase):
    id: UUID
    document_id: UUID
    parsed_markdown: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkBase(BaseModel):
    chunk_index: int
    heading: str | None = None
    raw_text: str
    page_number: int | None = None
    char_start: int
    char_end: int


class DocumentChunkCreate(DocumentChunkBase):
    document_version_id: UUID


class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    document_version_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkPreviewResponse(BaseModel):
    id: UUID
    chunk_index: int
    heading: str | None = None
    page_number: int | None = None
    preview_text: str


class AuditFlagBase(BaseModel):
    risk_level: str
    category: str
    issue_summary: str
    detailed_explanation: str
    playbook_counter_proposal: str | None = None
    status: str = "unresolved"


class AuditFlagCreate(AuditFlagBase):
    document_version_id: UUID
    document_chunk_id: UUID | None = None


class AuditFlagStatusUpdate(BaseModel):
    status: str


class AuditFlagResponse(AuditFlagBase):
    id: UUID
    document_version_id: UUID
    document_chunk_id: UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ObligationBase(BaseModel):
    title: str
    description: str | None = None
    due_date: date | None = None
    trigger_condition: str | None = None
    alert_lead_days: int = 30
    status: str = "pending"


class ObligationCreate(ObligationBase):
    document_id: UUID
    document_chunk_id: UUID | None = None


class ObligationStatusUpdate(BaseModel):
    status: str


class ObligationResponse(ObligationBase):
    id: UUID
    document_id: UUID
    document_chunk_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentRelationshipBase(BaseModel):
    relationship_type: str


class DocumentRelationshipCreate(DocumentRelationshipBase):
    source_document_id: UUID
    target_document_id: UUID


class DocumentRelationshipResponse(DocumentRelationshipBase):
    id: UUID
    source_document_id: UUID
    target_document_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentRelationshipSuccessResponse(BaseModel):
    id: UUID
    status: str


class ObligationPreviewResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    due_date: date | None = None
    status: str
    document_chunk_id: UUID | None = None


class DeepAnalysisViewResponse(BaseModel):
    document: DocumentResponse
    active_version: DocumentVersionResponse
    flag_summary: DocumentFlagSummary
    flags: list[AuditFlagResponse]
    chunk_count: int
    chunk_preview: list[DocumentChunkPreviewResponse]
    obligation_count: int
    obligations: list[ObligationPreviewResponse]
