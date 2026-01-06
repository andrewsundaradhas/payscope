from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass

from pypdf import PdfReader

from payscope_ingestion.models import FileFormat, PdfKind


@dataclass(frozen=True)
class Detection:
    file_format: FileFormat
    pdf_kind: PdfKind | None


def detect_file_format(head: bytes, filename: str, file_path: str) -> Detection:
    # PDF magic
    if head.startswith(b"%PDF-"):
        kind = detect_pdf_kind(file_path)
        return Detection(file_format=FileFormat.pdf, pdf_kind=kind)

    # ZIP (XLSX is a ZIP container)
    if head.startswith(b"PK\x03\x04"):
        if _is_xlsx_zip(file_path):
            return Detection(file_format=FileFormat.xlsx, pdf_kind=None)

    # Default to CSV if it looks like text with delimiters.
    if _looks_like_csv(file_path):
        return Detection(file_format=FileFormat.csv, pdf_kind=None)

    # Fallback based on extension if unknown. (Still no schema assumptions.)
    lower = filename.lower()
    if lower.endswith(".xlsx"):
        return Detection(file_format=FileFormat.xlsx, pdf_kind=None)
    if lower.endswith(".pdf"):
        return Detection(file_format=FileFormat.pdf, pdf_kind=detect_pdf_kind(file_path))
    return Detection(file_format=FileFormat.csv, pdf_kind=None)


def detect_pdf_kind(file_path: str) -> PdfKind:
    """
    Heuristic:
      - If any page yields meaningful extracted text -> DIGITAL
      - Else -> SCANNED
    """
    try:
        reader = PdfReader(file_path)
        for page in reader.pages[: min(5, len(reader.pages))]:
            text = (page.extract_text() or "").strip()
            if len(text) >= 40:
                return PdfKind.digital
        return PdfKind.scanned
    except Exception:
        return PdfKind.unknown


def _is_xlsx_zip(file_path: str) -> bool:
    try:
        with zipfile.ZipFile(file_path) as z:
            names = set(z.namelist())
            return "[Content_Types].xml" in names and any(n.startswith("xl/") for n in names)
    except Exception:
        return False


def _looks_like_csv(file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            sample = f.read(8192)
        # Basic decode attempt; allow UTF-8 with replacement
        text = sample.decode("utf-8", errors="replace")
        # csv.Sniffer can be overly permissive; require common delimiter presence
        if not any(d in text for d in [",", "\t", ";", "|"]):
            return False
        dialect = csv.Sniffer().sniff(text)
        # Confirm it parses at least 2 rows
        reader = csv.reader(io.StringIO(text), dialect)
        rows = 0
        for _ in reader:
            rows += 1
            if rows >= 2:
                return True
        return False
    except Exception:
        return False




