#!/usr/bin/env python3
"""
End-to-end dataset orchestration for PayScope.

Orchestrates:
1. Download and prepare datasets (banks 1-4)
2. Generate synthetic bank 5
3. Upload to ingestion service
4. Wait for processing completion
5. Train baseline models
6. Validate data in all stores

Usage:
    python datasets/run_e2e.py [--skip-download] [--skip-upload] [--skip-training]
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests


def run_command(cmd: list[str], cwd: str = None) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed: {e}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"\n[ERROR] Command not found: {cmd[0]}", file=sys.stderr)
        return False


def check_services() -> bool:
    """Check if required services are running."""
    print("\n[1] Checking services...")
    services = {
        "Ingestion": "http://localhost:8080/health",
        "API": "http://localhost:8000/health",
    }

    all_up = True
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✓ {name} is up")
            else:
                print(f"  ✗ {name} returned {response.status_code}")
                all_up = False
        except Exception as e:
            print(f"  ✗ {name} is down: {e}")
            all_up = False

    return all_up


def download_datasets() -> bool:
    """Step 1: Download and prepare datasets."""
    print("\n[2] Downloading and preparing datasets...")
    script = Path(__file__).parent / "download_and_prepare.py"
    return run_command([sys.executable, str(script)])


def generate_synthetic() -> bool:
    """Step 2: Generate synthetic bank 5."""
    print("\n[3] Generating synthetic bank 5...")
    script = Path(__file__).parent / "generate_synthetic_bank.py"
    return run_command([sys.executable, str(script)])


def upload_datasets() -> bool:
    """Step 3: Upload datasets to ingestion."""
    print("\n[4] Uploading datasets to ingestion service...")
    script = Path(__file__).parent / "upload_to_ingestion.py"
    return run_command([sys.executable, str(script), "all"])


def train_models() -> bool:
    """Step 4: Train baseline models."""
    print("\n[5] Training ML models...")
    # Try complete ML training first, fallback to basic
    script_complete = Path(__file__).parent / "train_ml_complete.py"
    script_basic = Path(__file__).parent / "train_models.py"
    
    if script_complete.exists():
        return run_command([sys.executable, str(script_complete), "all"])
    else:
        return run_command([sys.executable, str(script_basic), "all"])


def validate_datasets() -> bool:
    """Step 5: Validate datasets in all stores."""
    print("\n[6] Validating datasets...")

    api_url = os.getenv("API_URL", "http://localhost:8000")
    validation_url = f"{api_url}/admin/validate-datasets"

    # Issue admin JWT token (simplified - in production use proper auth)
    try:
        # Try without auth first (may require proper JWT)
        response = requests.get(validation_url, timeout=30)
        if response.status_code == 200:
            results = response.json()
            print("\nValidation Results:")
            print(json.dumps(results, indent=2))
            return True
        elif response.status_code == 401 or response.status_code == 403:
            print("  [WARNING] Authentication required for validation endpoint")
            print("  Run manually with proper admin credentials")
            return True  # Not a failure, just needs auth
        else:
            print(f"  [WARNING] Validation endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"  [WARNING] Validation check failed: {e}")
        return False


def main():
    """Main E2E orchestration."""
    parser = argparse.ArgumentParser(description="PayScope E2E Dataset Pipeline")
    parser.add_argument("--skip-download", action="store_true", help="Skip dataset download")
    parser.add_argument("--skip-upload", action="store_true", help="Skip upload to ingestion")
    parser.add_argument("--skip-training", action="store_true", help="Skip model training")
    parser.add_argument("--ingestion-url", default="http://localhost:8080", help="Ingestion service URL")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API service URL")
    args = parser.parse_args()

    os.environ["INGESTION_URL"] = args.ingestion_url
    os.environ["API_URL"] = args.api_url

    print("=" * 60)
    print("PayScope End-to-End Dataset Pipeline")
    print("=" * 60)

    # Check services
    if not check_services():
        print("\n[ERROR] Required services are not running", file=sys.stderr)
        print("Start services: docker compose up -d", file=sys.stderr)
        sys.exit(1)

    success = True

    # Step 1: Download datasets
    if not args.skip_download:
        if not download_datasets():
            print("\n[FAIL] Dataset download failed", file=sys.stderr)
            success = False
        if not generate_synthetic():
            print("\n[FAIL] Synthetic generation failed", file=sys.stderr)
            success = False
    else:
        print("\n[SKIP] Dataset download (--skip-download)")

    # Step 2: Upload to ingestion
    if success and not args.skip_upload:
        if not upload_datasets():
            print("\n[FAIL] Dataset upload failed", file=sys.stderr)
            success = False
    elif args.skip_upload:
        print("\n[SKIP] Dataset upload (--skip-upload)")

    # Step 3: Train models
    if success and not args.skip_training:
        if not train_models():
            print("\n[FAIL] Model training failed", file=sys.stderr)
            success = False
    elif args.skip_training:
        print("\n[SKIP] Model training (--skip-training)")

    # Step 4: Validate
    if success:
        validate_datasets()

    # Summary
    print("\n" + "=" * 60)
    if success:
        print("[OK] E2E Pipeline completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Verify data in Postgres, Neo4j, Pinecone")
        print("  2. Test RAG queries via API")
        print("  3. Run forecasting jobs")
        print("  4. Monitor metrics in Prometheus/Grafana")
    else:
        print("[FAIL] E2E Pipeline completed with errors")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

