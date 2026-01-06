"""
Report Upload and Processing API.

Features:
1. Multi-file upload (PDF, CSV, XLSX)
2. File type detection and validation
3. Async processing queue
4. Report metadata management
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/reports", tags=["reports"])


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------

class ReportMetadata(BaseModel):
    report_id: str
    filename: str
    file_type: Literal["pdf", "csv", "xlsx", "unknown"]
    file_size: int
    checksum: str
    upload_time: str
    status: Literal["uploaded", "processing", "parsed", "normalized", "error"]
    network: Optional[Literal["Visa", "Mastercard", "Unknown"]] = "Unknown"
    report_type: Optional[Literal["Authorization", "Settlement", "Clearing", "Unknown"]] = "Unknown"


class ReportSummary(BaseModel):
    report_id: str
    name: str
    type: str
    network: str
    row_count: int
    date_range: dict
    status: str


class ParsedData(BaseModel):
    report_id: str
    headers: list[str]
    row_count: int
    sample_rows: list[dict]
    detected_fields: dict[str, str]  # field_name -> detected_type
    confidence: float


class NormalizedTransaction(BaseModel):
    transaction_id: str
    timestamp: str
    network: str
    lifecycle_stage: Literal["AUTH", "CLEARING", "SETTLEMENT"]
    merchant_id: str
    merchant_name: str
    amount: float
    currency: str
    status: str
    response_code: Optional[str] = None


# --------------------------------------------------------------------------
# In-Memory Storage (Demo)
# --------------------------------------------------------------------------

MOCK_REPORTS: dict[str, ReportMetadata] = {}


def detect_file_type(filename: str, content: bytes) -> Literal["pdf", "csv", "xlsx", "unknown"]:
    """Detect file type from filename and magic bytes."""
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    
    # Check magic bytes
    if content[:4] == b"%PDF":
        return "pdf"
    elif content[:2] == b"PK":  # ZIP-based (XLSX)
        return "xlsx"
    elif ext == "csv" or b"," in content[:1000]:
        return "csv"
    elif ext == "xlsx":
        return "xlsx"
    elif ext == "pdf":
        return "pdf"
    
    return "unknown"


def detect_network(filename: str, content: bytes) -> Literal["Visa", "Mastercard", "Unknown"]:
    """Detect card network from filename or content."""
    filename_lower = filename.lower()
    content_str = content[:5000].decode("utf-8", errors="ignore").lower()
    
    if "visa" in filename_lower or "visa" in content_str:
        return "Visa"
    elif "mastercard" in filename_lower or "mc" in filename_lower or "mastercard" in content_str:
        return "Mastercard"
    
    return "Unknown"


def detect_report_type(filename: str, content: bytes) -> Literal["Authorization", "Settlement", "Clearing", "Unknown"]:
    """Detect report type from filename or content."""
    filename_lower = filename.lower()
    content_str = content[:5000].decode("utf-8", errors="ignore").lower()
    
    if any(word in filename_lower or word in content_str for word in ["auth", "authorization", "approve"]):
        return "Authorization"
    elif any(word in filename_lower or word in content_str for word in ["settle", "settlement", "batch"]):
        return "Settlement"
    elif any(word in filename_lower or word in content_str for word in ["clear", "clearing"]):
        return "Clearing"
    
    return "Unknown"


# --------------------------------------------------------------------------
# API Endpoints
# --------------------------------------------------------------------------

@router.post("/upload", response_model=ReportMetadata)
async def upload_report(file: UploadFile = File(...)) -> ReportMetadata:
    """
    Upload a payment report file (PDF, CSV, or XLSX).
    
    Returns metadata and queues the file for async processing.
    """
    content = await file.read()
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
    if len(content) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    
    report_id = str(uuid.uuid4())
    checksum = hashlib.sha256(content).hexdigest()
    file_type = detect_file_type(file.filename or "unknown", content)
    network = detect_network(file.filename or "", content)
    report_type = detect_report_type(file.filename or "", content)
    
    metadata = ReportMetadata(
        report_id=report_id,
        filename=file.filename or "unknown",
        file_type=file_type,
        file_size=len(content),
        checksum=checksum,
        upload_time=datetime.utcnow().isoformat(),
        status="uploaded",
        network=network,
        report_type=report_type,
    )
    
    # Store in memory (in production, use S3/MinIO + database)
    MOCK_REPORTS[report_id] = metadata
    
    # In production: queue processing job
    # celery_client.queue_parsing_job(report_id, content)
    
    return metadata


@router.get("/list", response_model=list[ReportSummary])
async def list_reports() -> list[ReportSummary]:
    """List all uploaded reports."""
    summaries = []
    for report_id, meta in MOCK_REPORTS.items():
        summaries.append(ReportSummary(
            report_id=report_id,
            name=meta.filename,
            type=meta.report_type or "Unknown",
            network=meta.network or "Unknown",
            row_count=0,  # Would come from parsed data
            date_range={"start": "2025-01-01", "end": "2025-01-07"},
            status=meta.status,
        ))
    
    # Add mock reports for demo
    if not summaries:
        summaries = [
            ReportSummary(
                report_id="r_auth_visa_dec",
                name="Authorization Summary — Dec 18–24 (Visa)",
                type="Authorization",
                network="Visa",
                row_count=168,
                date_range={"start": "2025-12-18", "end": "2025-12-24"},
                status="normalized",
            ),
            ReportSummary(
                report_id="r_auth_mc_dec",
                name="Authorization Summary — Dec 18–24 (Mastercard)",
                type="Authorization",
                network="Mastercard",
                row_count=168,
                date_range={"start": "2025-12-18", "end": "2025-12-24"},
                status="normalized",
            ),
            ReportSummary(
                report_id="r_settle_visa_dec",
                name="Settlement Batch — Dec 11–24 (Visa)",
                type="Settlement",
                network="Visa",
                row_count=14,
                date_range={"start": "2025-12-11", "end": "2025-12-24"},
                status="normalized",
            ),
            ReportSummary(
                report_id="r_settle_mc_dec",
                name="Settlement Batch — Dec 11–24 (Mastercard)",
                type="Settlement",
                network="Mastercard",
                row_count=14,
                date_range={"start": "2025-12-11", "end": "2025-12-24"},
                status="normalized",
            ),
        ]
    
    return summaries


@router.get("/{report_id}", response_model=ReportMetadata)
async def get_report(report_id: str) -> ReportMetadata:
    """Get metadata for a specific report."""
    if report_id in MOCK_REPORTS:
        return MOCK_REPORTS[report_id]
    
    # Return mock data for demo reports
    if report_id.startswith("r_"):
        return ReportMetadata(
            report_id=report_id,
            filename=f"{report_id}.csv",
            file_type="csv",
            file_size=1024,
            checksum="mock_checksum",
            upload_time="2025-01-01T00:00:00",
            status="normalized",
            network="Visa" if "visa" in report_id else "Mastercard",
            report_type="Authorization" if "auth" in report_id else "Settlement",
        )
    
    raise HTTPException(status_code=404, detail="Report not found")


@router.get("/{report_id}/parsed", response_model=ParsedData)
async def get_parsed_data(report_id: str) -> ParsedData:
    """Get parsed data from a report."""
    # Mock parsed data
    return ParsedData(
        report_id=report_id,
        headers=["transaction_id", "timestamp", "merchant_id", "amount", "currency", "status"],
        row_count=168,
        sample_rows=[
            {
                "transaction_id": "txn_001",
                "timestamp": "2025-12-18T10:30:00Z",
                "merchant_id": "m_athena",
                "amount": "125.50",
                "currency": "USD",
                "status": "approved",
            },
            {
                "transaction_id": "txn_002",
                "timestamp": "2025-12-18T10:35:00Z",
                "merchant_id": "m_orbit",
                "amount": "89.99",
                "currency": "USD",
                "status": "approved",
            },
        ],
        detected_fields={
            "transaction_id": "identifier",
            "timestamp": "datetime",
            "merchant_id": "identifier",
            "amount": "currency_amount",
            "currency": "currency_code",
            "status": "categorical",
        },
        confidence=0.92,
    )


@router.get("/{report_id}/transactions", response_model=list[NormalizedTransaction])
async def get_transactions(report_id: str, limit: int = 100) -> list[NormalizedTransaction]:
    """Get normalized transactions from a report."""
    # Generate mock transactions
    import random
    random.seed(hash(report_id) % (2**32))
    
    transactions = []
    network = "Visa" if "visa" in report_id.lower() else "Mastercard"
    lifecycle = "AUTH" if "auth" in report_id.lower() else "SETTLEMENT"
    
    merchants = [
        ("m_athena", "Athena Grocers"),
        ("m_orbit", "Orbit Electronics"),
        ("m_summit", "Summit Travel"),
        ("m_bistro", "Bistro North"),
    ]
    
    for i in range(min(limit, 50)):
        merchant = random.choice(merchants)
        status = random.choice(["approved", "approved", "approved", "declined"])
        
        transactions.append(NormalizedTransaction(
            transaction_id=f"txn_{report_id}_{i:04d}",
            timestamp=f"2025-12-{random.randint(18, 24):02d}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00Z",
            network=network,
            lifecycle_stage=lifecycle,
            merchant_id=merchant[0],
            merchant_name=merchant[1],
            amount=round(random.uniform(10, 500), 2),
            currency="USD",
            status=status,
            response_code="00" if status == "approved" else random.choice(["05", "51", "91"]),
        ))
    
    return transactions


@router.post("/{report_id}/process")
async def trigger_processing(report_id: str) -> dict:
    """Trigger async processing of a report."""
    if report_id not in MOCK_REPORTS:
        # Accept mock report IDs
        if not report_id.startswith("r_"):
            raise HTTPException(status_code=404, detail="Report not found")
    
    # In production: trigger Celery task
    # from payscope_ingestion.celery_client import queue_parsing_job
    # queue_parsing_job(report_id)
    
    return {
        "report_id": report_id,
        "status": "processing_queued",
        "message": "Report processing has been queued",
    }


@router.delete("/{report_id}")
async def delete_report(report_id: str) -> dict:
    """Delete a report and its data."""
    if report_id in MOCK_REPORTS:
        del MOCK_REPORTS[report_id]
        return {"status": "deleted", "report_id": report_id}
    
    raise HTTPException(status_code=404, detail="Report not found")

