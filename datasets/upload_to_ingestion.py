#!/usr/bin/env python3
"""
Upload prepared datasets to PayScope ingestion service.

Uses existing /upload endpoint with X-Bank-Id header.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List

import requests


def upload_dataset(
    csv_path: Path, bank_id: int, ingestion_url: str = "http://localhost:8080"
) -> Dict:
    """
    Upload a CSV file to ingestion service.

    Returns upload result with report_id.
    """
    url = f"{ingestion_url}/upload"

    headers = {
        "X-Bank-Id": str(bank_id),
        "X-Uploader": "dataset_loader",
    }

    with open(csv_path, "rb") as f:
        files = {"files": (csv_path.name, f, "text/csv")}
        response = requests.post(url, headers=headers, files=files, timeout=300)

    if response.status_code not in [200, 201]:
        raise RuntimeError(
            f"Upload failed: {response.status_code} - {response.text}"
        )

    result = response.json()
    if "errors" in result and result["errors"]:
        raise RuntimeError(f"Upload errors: {result['errors']}")

    if "uploads" not in result or not result["uploads"]:
        raise RuntimeError(f"No upload results: {result}")

    return result["uploads"][0]  # Return first upload result


def wait_for_processing(
    report_id: str,
    database_url: str,
    max_wait_minutes: int = 30,
    check_interval_seconds: int = 10,
) -> bool:
    """
    Wait for Celery job to complete processing.

    Checks parse_jobs table for SUCCESS status.
    """
    try:
        import asyncpg

        async def check_status():
            conn = await asyncpg.connect(database_url)
            try:
                result = await conn.fetchrow(
                    """
                    SELECT pj.status, pj.error
                    FROM parse_jobs pj
                    JOIN report_uploads ru ON ru.artifact_id = pj.artifact_id
                    WHERE ru.report_id = $1::uuid
                    ORDER BY pj.updated_at DESC
                    LIMIT 1
                    """,
                    report_id,
                )
                if result:
                    return result["status"], result.get("error")
                return None, None
            finally:
                await conn.close()

        import asyncio

        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60

        while time.time() - start_time < max_wait_seconds:
            status, error = asyncio.run(check_status())
            if status == "SUCCESS":
                return True
            if status == "FAILED":
                raise RuntimeError(f"Processing failed: {error}")
            if status is None:
                print(f"  Waiting for job to appear... ({int(time.time() - start_time)}s)")
            else:
                print(f"  Status: {status} ({int(time.time() - start_time)}s)")

            time.sleep(check_interval_seconds)

        raise TimeoutError(
            f"Processing did not complete within {max_wait_minutes} minutes"
        )

    except ImportError:
        print(
            "[WARNING] asyncpg not available, skipping status check",
            file=sys.stderr,
        )
        print("  Install with: pip install asyncpg", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[WARNING] Status check failed: {e}", file=sys.stderr)
        return False


def main():
    """Upload all prepared datasets."""
    if len(sys.argv) < 2:
        print("Usage: python upload_to_ingestion.py <bank_id> [ingestion_url]")
        print("  Or: python upload_to_ingestion.py all")
        sys.exit(1)

    ingestion_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8080"

    bank_ids = []
    if sys.argv[1] == "all":
        bank_ids = [1, 2, 3, 4, 5]
    else:
        bank_ids = [int(sys.argv[1])]

    print("=" * 60)
    print("Uploading Datasets to Ingestion Service")
    print("=" * 60)
    print(f"Ingestion URL: {ingestion_url}\n")

    database_url = os.getenv("DATABASE_URL", "postgresql://payscope:payscope@localhost:5432/payscope")

    results = {}
    for bank_id in bank_ids:
        csv_file = Path(f"datasets/processed/bank_{bank_id}/bank_{bank_id}_processed.csv")
        if not csv_file.exists():
            print(f"[SKIP] Bank {bank_id}: File not found: {csv_file}")
            continue

        print(f"[Bank {bank_id}] Uploading {csv_file.name}...")
        try:
            upload_result = upload_dataset(csv_file, bank_id, ingestion_url)
            report_id = upload_result["report_id"]
            print(f"  [OK] Uploaded - report_id: {report_id}")

            # Wait for processing
            print("  Waiting for processing to complete...")
            if wait_for_processing(report_id, database_url):
                print(f"  [OK] Processing completed successfully")
                results[bank_id] = {"status": "success", "report_id": report_id}
            else:
                print(f"  [WARNING] Could not verify processing completion")
                results[bank_id] = {"status": "uploaded", "report_id": report_id}

        except Exception as e:
            print(f"  [FAIL] {e}", file=sys.stderr)
            results[bank_id] = {"status": "failed", "error": str(e)}
            continue

        print()

    print("=" * 60)
    print("Upload Summary")
    print("=" * 60)
    for bank_id, result in results.items():
        status = result["status"]
        if status == "success":
            print(f"  Bank {bank_id}: ✓ Success")
        elif status == "uploaded":
            print(f"  Bank {bank_id}: ⚠ Uploaded (verification skipped)")
        else:
            print(f"  Bank {bank_id}: ✗ Failed - {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()



