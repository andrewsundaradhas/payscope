"""
Report discovery module for collecting and processing sample payment reports.

Discovers publicly available payment report samples and prepares them for ingestion.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
import pandas as pd

from payscope_processing.contracts import SourceFileRef
from payscope_processing.storage import build_s3_client


@dataclass
class ReportSample:
    """Represents a discovered report sample."""
    source_url: str
    report_type: str  # "authorization" | "settlement" | "clearing" | "combined"
    format: str  # "PDF" | "CSV" | "XLSX"
    description: str
    metadata: Dict[str, Any]


class ReportDiscovery:
    """
    Discovers and collects sample payment reports from public sources.
    
    Lightweight collection: focuses on representative samples, not exhaustive datasets.
    """

    def __init__(self, storage_dir: Path = None, s3_client=None):
        self.storage_dir = storage_dir or Path("discovery/samples")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.s3_client = s3_client

    def discover_sample_reports(self) -> List[ReportSample]:
        """
        Discover sample reports from curated public sources.
        
        Returns:
            List of ReportSample objects
        """
        samples = []

        # Sample sources (lightweight, non-proprietary examples)
        # In production, these would be configurable or come from a registry
        
        # Example: Public financial report samples
        # Note: In real implementation, use actual public report sources
        # For now, this is a framework that can be extended

        return samples

    def download_report(
        self,
        sample: ReportSample,
        output_path: Path = None,
    ) -> Path:
        """
        Download a report sample.
        
        Returns:
            Path to downloaded file
        """
        if output_path is None:
            # Generate path based on source URL hash
            url_hash = hashlib.sha256(sample.source_url.encode()).hexdigest()[:16]
            ext = sample.format.lower()
            output_path = self.storage_dir / f"{sample.report_type}_{url_hash}.{ext}"

        # Download
        response = httpx.get(sample.source_url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()

        output_path.write_bytes(response.content)

        return output_path

    def store_sample_metadata(
        self,
        sample: ReportSample,
        file_path: Path,
    ) -> Path:
        """
        Store metadata about a sample report.
        
        Returns:
            Path to metadata file
        """
        metadata_file = file_path.with_suffix(".metadata.json")
        
        metadata = {
            "source_url": sample.source_url,
            "report_type": sample.report_type,
            "format": sample.format,
            "description": sample.description,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "file_hash": hashlib.sha256(file_path.read_bytes()).hexdigest(),
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            **sample.metadata,
        }

        metadata_file.write_text(json.dumps(metadata, indent=2))
        return metadata_file

    def prepare_for_ingestion(
        self,
        file_path: Path,
        report_type: str,
        bank_id: str = "discovery",
    ) -> Dict[str, Any]:
        """
        Prepare a discovered report for ingestion pipeline.
        
        Returns:
            Dict with ingestion metadata
        """
        # Generate checksum
        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()

        # Detect format
        ext = file_path.suffix.lower()
        format_map = {
            ".pdf": "PDF",
            ".csv": "CSV",
            ".xlsx": ".XLSX",
            ".xls": "XLSX",
        }
        detected_format = format_map.get(ext, "UNKNOWN")

        return {
            "file_path": str(file_path),
            "file_format": detected_format,
            "checksum": file_hash,
            "report_type": report_type,
            "bank_id": bank_id,
            "source": "discovery",
            "metadata": {
                "discovered": True,
                "discovery_time": datetime.now(timezone.utc).isoformat(),
            },
        }


def discover_and_prepare_samples(
    output_dir: Path = None,
    max_samples: int = 10,
) -> List[Dict[str, Any]]:
    """
    Discover sample reports and prepare them for ingestion.
    
    Args:
        output_dir: Directory to store samples
        max_samples: Maximum number of samples to collect
    
    Returns:
        List of prepared sample metadata
    """
    discovery = ReportDiscovery(storage_dir=output_dir)
    
    samples = discovery.discover_sample_reports()
    prepared = []
    
    for sample in samples[:max_samples]:
        try:
            # Download
            file_path = discovery.download_report(sample)
            
            # Store metadata
            discovery.store_sample_metadata(sample, file_path)
            
            # Prepare for ingestion
            ingestion_meta = discovery.prepare_for_ingestion(
                file_path,
                sample.report_type,
            )
            prepared.append(ingestion_meta)
            
        except Exception as e:
            # Log and continue
            print(f"Failed to process sample {sample.source_url}: {e}")
            continue
    
    return prepared



