from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class FileFormat(str, enum.Enum):
    pdf = "PDF"
    csv = "CSV"
    xlsx = "XLSX"


class PdfKind(str, enum.Enum):
    scanned = "SCANNED"
    digital = "DIGITAL"
    unknown = "UNKNOWN"


class JobStatus(str, enum.Enum):
    queued = "QUEUED"
    started = "STARTED"
    success = "SUCCESS"
    failed = "FAILED"


class Artifact(Base):
    __tablename__ = "artifacts"

    artifact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    file_format: Mapped[FileFormat] = mapped_column(Enum(FileFormat, name="file_format"), nullable=False)
    pdf_kind: Mapped[PdfKind | None] = mapped_column(Enum(PdfKind, name="pdf_kind"), nullable=True)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parse_job: Mapped["ParseJob"] = relationship(back_populates="artifact", uselist=False)


class ParseJob(Base):
    __tablename__ = "parse_jobs"
    __table_args__ = (UniqueConstraint("artifact_id", name="uq_parse_jobs_artifact_id"),)

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("artifacts.artifact_id"), nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status"), nullable=False, default=JobStatus.queued)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    artifact: Mapped[Artifact] = relationship(back_populates="parse_job")


class ReportUpload(Base):
    __tablename__ = "report_uploads"

    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("artifacts.artifact_id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    upload_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    uploader: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    artifact: Mapped[Artifact] = relationship()


class ExtractionStage(str, enum.Enum):
    intermediate = "INTERMEDIATE"
    layout = "LAYOUT"


class ExtractedDocument(Base):
    __tablename__ = "extracted_documents"
    __table_args__ = (UniqueConstraint("artifact_id", "stage", name="uq_extracted_documents_artifact_stage"),)

    extracted_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("artifacts.artifact_id"), nullable=False, index=True)
    stage: Mapped[ExtractionStage] = mapped_column(Enum(ExtractionStage, name="extraction_stage"), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    artifact: Mapped[Artifact] = relationship()


