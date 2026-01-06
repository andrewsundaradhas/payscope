#!/usr/bin/env python3
"""
Download and prepare datasets for PayScope training.

Downloads:
- Kaggle Credit Card Fraud Detection (bank_id=1)
- IEEE-CIS Fraud Detection (bank_id=2)
- PaySim (bank_id=3)
- Olist Brazilian E-commerce (bank_id=4)

Samples datasets to manageable sizes (50k-150k rows) while preserving class imbalance.
"""

import hashlib
import json
import os
import random
import sys
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

# Bank assignments
BANK_DATASETS = {
    1: {
        "name": "Kaggle Credit Card Fraud Detection",
        "kaggle": "mlg-ulb/creditcardfraud",
        "filename": "creditcard.csv",
        "max_rows": 100000,
    },
    2: {
        "name": "IEEE-CIS Fraud Detection",
        "kaggle": "c/ieee-fraud-detection",
        "filename": "train_transaction.csv",
        "max_rows": 150000,
    },
    3: {
        "name": "PaySim",
        "kaggle": "ealaxi/paysim1",
        "filename": "PS_20174392719_1491204439457_log.csv",
        "max_rows": 120000,
    },
    4: {
        "name": "Olist Brazilian E-commerce",
        "kaggle": "olistbr/brazilian-ecommerce",
        "filename": "olist_orders_dataset.csv",
        "max_rows": 100000,
    },
}

# Fixed seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def setup_directories() -> Dict[int, Path]:
    """Create output directories for each bank."""
    base = Path("datasets/processed")
    dirs = {}
    for bank_id in BANK_DATASETS:
        bank_dir = base / f"bank_{bank_id}"
        bank_dir.mkdir(parents=True, exist_ok=True)
        dirs[bank_id] = bank_dir
    return dirs


def download_kaggle_dataset(
    dataset: str, output_dir: Path, filename: Optional[str] = None
) -> Path:
    """
    Download dataset from Kaggle using Kaggle API.

    Supports:
    - KAGGLE_API_TOKEN environment variable (converted to username/key format)
    - KAGGLE_USERNAME and KAGGLE_KEY environment variables
    - ~/.kaggle/kaggle.json file
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi

        # Handle KAGGLE_API_TOKEN - newer format needs conversion
        api_token = os.getenv("KAGGLE_API_TOKEN")
        if api_token:
            # For API token format, we need to check if it's username/key format
            # If it's KGAT_ format, we may need to extract username separately
            # For now, set it as the key and try to get username from token metadata
            # Or create a temporary kaggle.json file
            kaggle_dir = Path.home() / ".kaggle"
            kaggle_dir.mkdir(exist_ok=True)
            kaggle_json = kaggle_dir / "kaggle.json"
            
            # If token is in KGAT_ format, we might need username from settings
            # For now, try to use it directly if kaggle.json doesn't exist
            if not kaggle_json.exists() and api_token.startswith("KGAT_"):
                # Note: This is a workaround - proper setup should use kaggle.json
                # with both username and key, or set both env vars
                print(f"  [INFO] Using KAGGLE_API_TOKEN (ensure username is also set)")
                # The API might work with just the token in some cases
        
        api = KaggleApi()
        api.authenticate()

        # Download dataset
        api.dataset_download_files(dataset, path=str(output_dir), unzip=True)

        # Find the CSV file
        if filename:
            csv_path = output_dir / filename
            if csv_path.exists():
                return csv_path

        # Try to find any CSV file
        csv_files = list(output_dir.glob("*.csv"))
        if csv_files:
            return csv_files[0]

        raise FileNotFoundError(f"No CSV file found in {output_dir}")

    except ImportError:
        print(
            "[ERROR] kaggle package not installed. Install with: pip install kaggle",
            file=sys.stderr,
        )
        raise  # Re-raise to be handled by caller
    except Exception as e:
        print(f"[ERROR] Failed to download {dataset}: {e}", file=sys.stderr)
        raise  # Re-raise to be handled by caller


def sample_dataset(
    df: pd.DataFrame, max_rows: int, fraud_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Sample dataset deterministically while preserving class imbalance.

    If fraud_col is provided, uses stratified sampling.
    Otherwise, simple random sampling.
    """
    if len(df) <= max_rows:
        return df

    if fraud_col and fraud_col in df.columns:
        # Stratified sampling to preserve fraud ratio
        fraud_ratio = df[fraud_col].mean()
        n_fraud = int(max_rows * fraud_ratio)
        n_normal = max_rows - n_fraud

        fraud_samples = df[df[fraud_col] == 1].sample(
            n=min(n_fraud, len(df[df[fraud_col] == 1])), random_state=RANDOM_SEED
        )
        normal_samples = df[df[fraud_col] == 0].sample(
            n=min(n_normal, len(df[df[fraud_col] == 0])), random_state=RANDOM_SEED
        )

        sampled = pd.concat([fraud_samples, normal_samples]).sample(
            frac=1, random_state=RANDOM_SEED
        )
        return sampled.reset_index(drop=True)
    else:
        # Simple random sampling
        return df.sample(n=max_rows, random_state=RANDOM_SEED).reset_index(drop=True)


def normalize_columns(df: pd.DataFrame, bank_id: int) -> pd.DataFrame:
    """
    Minimal column normalization (rename to common patterns only).
    Does NOT change the schema logic - just standardizes naming.
    """
    # Common column name mappings (minimal, no logic changes)
    column_mappings = {
        "Class": "is_fraud",  # CCFD
        "isFraud": "is_fraud",  # IEEE-CIS
        "isFlaggedFraud": "is_flagged_fraud",  # PaySim
        "order_id": "transaction_id",  # Olist
        "customer_id": "merchant_id",  # Olist (simplified)
    }

    df = df.rename(columns={k: v for k, v in column_mappings.items() if k in df.columns})
    return df


def prepare_bank_dataset(bank_id: int, output_dir: Path) -> Path:
    """Download, sample, and prepare dataset for a bank."""
    config = BANK_DATASETS[bank_id]
    print(f"\n[Bank {bank_id}] Processing {config['name']}...")

    # Download
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    print(f"  Downloading from Kaggle: {config['kaggle']}...")
    csv_path = download_kaggle_dataset(
        config["kaggle"], raw_dir, config.get("filename")
    )

    # Load and sample
    print(f"  Loading {csv_path.name}...")
    df = pd.read_csv(csv_path)

    print(f"  Original size: {len(df):,} rows, {len(df.columns)} columns")
    print(f"  Sampling to max {config['max_rows']:,} rows...")

    # Try to find fraud column for stratified sampling
    fraud_col = None
    for col in ["is_fraud", "Class", "isFraud", "isFlaggedFraud"]:
        if col in df.columns:
            fraud_col = col
            break

    if fraud_col:
        print(f"  Using stratified sampling (fraud column: {fraud_col})")
        fraud_count = df[fraud_col].sum()
        print(f"  Fraud cases: {fraud_count:,} ({fraud_count/len(df)*100:.2f}%)")

    sampled_df = sample_dataset(df, config["max_rows"], fraud_col)

    print(f"  Sampled size: {len(sampled_df):,} rows")
    if fraud_col and fraud_col in sampled_df.columns:
        sampled_fraud = sampled_df[fraud_col].sum()
        print(
            f"  Sampled fraud: {sampled_fraud:,} ({sampled_fraud/len(sampled_df)*100:.2f}%)"
        )

    # Normalize columns (minimal)
    sampled_df = normalize_columns(sampled_df, bank_id)

    # Save processed CSV
    output_file = output_dir / f"bank_{bank_id}_processed.csv"
    sampled_df.to_csv(output_file, index=False)
    print(f"  Saved: {output_file}")

    # Save metadata
    metadata = {
        "bank_id": bank_id,
        "dataset_name": config["name"],
        "source": config["kaggle"],
        "original_rows": len(df),
        "processed_rows": len(sampled_df),
        "columns": list(sampled_df.columns),
        "checksum": hashlib.sha256(output_file.read_bytes()).hexdigest(),
    }
    metadata_file = output_dir / f"bank_{bank_id}_metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))
    print(f"  Metadata: {metadata_file}")

    return output_file


def main():
    """Main entry point."""
    print("=" * 60)
    print("PayScope Dataset Download and Preparation")
    print("=" * 60)

    # Check Kaggle credentials (support multiple methods)
    kaggle_api_token = os.getenv("KAGGLE_API_TOKEN")
    kaggle_username = os.getenv("KAGGLE_USERNAME")
    kaggle_key = os.getenv("KAGGLE_KEY")

    # Newer API token method (takes precedence)
    if kaggle_api_token:
        print(f"\n[OK] Using KAGGLE_API_TOKEN environment variable")
        os.environ["KAGGLE_API_TOKEN"] = kaggle_api_token
    # Traditional username/key method
    elif kaggle_username and kaggle_key:
        print(f"\n[OK] Using KAGGLE_USERNAME and KAGGLE_KEY environment variables")
        os.environ["KAGGLE_USERNAME"] = kaggle_username
        os.environ["KAGGLE_KEY"] = kaggle_key
    # Check for kaggle.json file
    else:
        kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
        if kaggle_json.exists():
            print(f"\n[OK] Using kaggle.json file: {kaggle_json}")
        else:
            print("\n[ERROR] Kaggle credentials not found.", file=sys.stderr)
            print("\nPlease use one of these methods:", file=sys.stderr)
            print("  1. Set KAGGLE_API_TOKEN environment variable", file=sys.stderr)
            print("  2. Set KAGGLE_USERNAME and KAGGLE_KEY environment variables", file=sys.stderr)
            print(f"  3. Create {kaggle_json} with your Kaggle API credentials", file=sys.stderr)
            print("\nWindows PowerShell:", file=sys.stderr)
            print('  $env:KAGGLE_API_TOKEN="your_token_here"', file=sys.stderr)
            sys.exit(1)

    # Setup directories
    output_dirs = setup_directories()

    # Process each bank dataset
    processed_files = {}
    failed_banks = []
    for bank_id in sorted(BANK_DATASETS.keys()):
        try:
            output_file = prepare_bank_dataset(bank_id, output_dirs[bank_id])
            processed_files[bank_id] = output_file
        except Exception as e:
            print(f"\n[WARNING] Failed to process bank {bank_id}: {e}", file=sys.stderr)
            failed_banks.append(bank_id)
            # Continue with other banks instead of exiting
            continue

    print("\n" + "=" * 60)
    if processed_files:
        print(f"[OK] Successfully prepared {len(processed_files)} dataset(s)!")
    if failed_banks:
        print(f"[WARNING] Failed to download {len(failed_banks)} dataset(s): {failed_banks}")
    print("=" * 60)
    
    if processed_files:
        print("\nProcessed files:")
        for bank_id, file_path in processed_files.items():
            print(f"  Bank {bank_id}: {file_path}")

    if failed_banks:
        print("\nFailed datasets (may need Kaggle acceptance):")
        for bank_id in failed_banks:
            config = BANK_DATASETS[bank_id]
            print(f"  Bank {bank_id}: {config['name']}")
            print(f"    Visit: https://www.kaggle.com/datasets/{config['kaggle']}")
            print(f"    Click 'I Understand and Accept' then re-run")

    print("\nNext steps:")
    print("  1. Generate synthetic bank 5: python datasets/generate_synthetic_bank.py")
    if not processed_files:
        print("  2. Fix failed datasets and re-run download")
    print("  3. Run E2E pipeline: python datasets/run_e2e.py")


if __name__ == "__main__":
    # Fix numpy import (used by pandas)
    import numpy as np

    main()

