from datetime import datetime, date
from uuid import UUID, uuid4
from sqlalchemy import DateTime, Date, String, Integer, Text, Boolean, ForeignKey, CheckConstraint, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    clerk_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    documents: Mapped[list["Document"]] = relationship(back_populates="user", cascade="all, delete-orphan", lazy="selectin")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    current_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("document_versions.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="documents", lazy="selectin")
    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document", foreign_keys="DocumentVersion.document_id", cascade="all, delete-orphan", lazy="selectin")
    current_version: Mapped["DocumentVersion | None"] = relationship(foreign_keys=[current_version_id], lazy="selectin")
    obligations: Mapped[list["Obligation"]] = relationship(back_populates="document", cascade="all, delete-orphan", lazy="selectin")
    source_relationships: Mapped[list["DocumentRelationship"]] = relationship(
        foreign_keys="DocumentRelationship.source_document_id",
        cascade="all, delete-orphan",
        lazy="selectin",
        back_populates="source_document"
    )
    target_relationships: Mapped[list["DocumentRelationship"]] = relationship(
        foreign_keys="DocumentRelationship.target_document_id",
        cascade="all, delete-orphan",
        lazy="selectin",
        back_populates="target_document"
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    parsed_markdown: Mapped[str | None] = mapped_column(Text)
    is_signed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="versions", foreign_keys=[document_id], lazy="selectin")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document_version", cascade="all, delete-orphan", lazy="selectin")
    audit_flags: Mapped[list["AuditFlag"]] = relationship(back_populates="document_version", cascade="all, delete-orphan", lazy="selectin")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_version_id: Mapped[UUID] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str | None] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document_version: Mapped["DocumentVersion"] = relationship(back_populates="chunks", lazy="selectin")
    audit_flags: Mapped[list["AuditFlag"]] = relationship(back_populates="document_chunk", lazy="selectin")
    obligations: Mapped[list["Obligation"]] = relationship(back_populates="document_chunk", lazy="selectin")


class AuditFlag(Base):
    __tablename__ = "audit_flags"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_version_id: Mapped[UUID] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False)
    document_chunk_id: Mapped[UUID | None] = mapped_column(ForeignKey("document_chunks.id", ondelete="SET NULL"))
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_summary: Mapped[str] = mapped_column(String(255), nullable=False)
    detailed_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    playbook_counter_proposal: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="unresolved")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document_version: Mapped["DocumentVersion"] = relationship(back_populates="audit_flags", lazy="selectin")
    document_chunk: Mapped["DocumentChunk | None"] = relationship(back_populates="audit_flags", lazy="selectin")


class Obligation(Base):
    __tablename__ = "obligations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    document_chunk_id: Mapped[UUID | None] = mapped_column(ForeignKey("document_chunks.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    trigger_condition: Mapped[str | None] = mapped_column(Text)
    alert_lead_days: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    document: Mapped["Document"] = relationship(back_populates="obligations", lazy="selectin")
    document_chunk: Mapped["DocumentChunk | None"] = relationship(back_populates="obligations", lazy="selectin")


class DocumentRelationship(Base):
    __tablename__ = "document_relationships"

    __table_args__ = (
        CheckConstraint("source_document_id <> target_document_id", name="chk_self_reference"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    target_document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_document: Mapped["Document"] = relationship(
        foreign_keys=[source_document_id],
        lazy="selectin",
        back_populates="source_relationships"
    )
    target_document: Mapped["Document"] = relationship(
        foreign_keys=[target_document_id],
        lazy="selectin",
        back_populates="target_relationships"
    )


class AIInferenceLog(Base):
    __tablename__ = "ai_inference_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"))
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cached_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0.000000)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status_code: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(foreign_keys=[user_id], lazy="selectin")
    document: Mapped["Document | None"] = relationship(foreign_keys=[document_id], lazy="selectin")


class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)
    queue_name: Mapped[str] = mapped_column(String(50), nullable=False, default="high_priority")
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    current_retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    worker_node_id: Mapped[str | None] = mapped_column(String(100))
    error_payload: Mapped[dict | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(foreign_keys=[document_id], lazy="selectin")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(50), nullable=False)
    context_precision: Mapped[float | None] = mapped_column(Numeric(4, 3))
    context_recall: Mapped[float | None] = mapped_column(Numeric(4, 3))
    faithfulness: Mapped[float | None] = mapped_column(Numeric(4, 3))
    answer_relevance: Mapped[float | None] = mapped_column(Numeric(4, 3))
    test_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    passed_threshold: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
