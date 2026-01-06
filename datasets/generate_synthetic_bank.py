#!/usr/bin/env python3
"""
Generate synthetic dataset for bank_id=5.

Mixes 10-20% rows from each real dataset (banks 1-4) and applies
statistical perturbation to create a realistic synthetic dataset.
"""

import json
import random
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

# Fixed seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

BANK_IDS = [1, 2, 3, 4]
TARGET_ROWS = 100000  # Target size for bank 5
MIN_SAMPLE_RATIO = 0.10  # 10% minimum from each bank
MAX_SAMPLE_RATIO = 0.20  # 20% maximum from each bank


def load_bank_data(bank_id: int) -> pd.DataFrame:
    """Load processed dataset for a bank."""
    bank_file = Path(f"datasets/processed/bank_{bank_id}/bank_{bank_id}_processed.csv")
    if not bank_file.exists():
        raise FileNotFoundError(f"Bank {bank_id} dataset not found: {bank_file}")
    return pd.read_csv(bank_file)


def jitter_amount(amount: float, noise_ratio: float = 0.05) -> float:
    """Add small random jitter to amount (5% max)."""
    jitter = amount * noise_ratio * (random.random() * 2 - 1)  # -5% to +5%
    return max(0.01, amount + jitter)  # Ensure positive


def shift_timestamp(timestamp_str: str, days_range: int = 30) -> str:
    """Shift timestamp by random days (preserves format)."""
    try:
        from dateutil.parser import parse
        from datetime import timedelta

        dt = parse(timestamp_str)
        shift_days = random.randint(-days_range, days_range)
        shifted = dt + timedelta(days=shift_days)
        return shifted.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp_str  # Return original if parsing fails


def add_noise_to_categorical(value: str, noise_prob: float = 0.05) -> str:
    """With small probability, replace categorical value."""
    if random.random() < noise_prob:
        # Add small suffix or prefix
        return f"{value}_synth{random.randint(1, 1000)}"
    return value


def mix_and_augment_datasets() -> pd.DataFrame:
    """Mix datasets from banks 1-4 and apply augmentation."""
    print("Loading datasets from banks 1-4...")
    datasets = {}
    for bank_id in BANK_IDS:
        try:
            df = load_bank_data(bank_id)
            datasets[bank_id] = df
            print(f"  Bank {bank_id}: {len(df):,} rows, {len(df.columns)} columns")
        except FileNotFoundError as e:
            print(f"  [WARNING] {e}", file=sys.stderr)
            continue

    if not datasets:
        raise RuntimeError("No datasets found to mix")

    # Sample rows from each dataset
    print(f"\nSampling {MIN_SAMPLE_RATIO*100:.0f}-{MAX_SAMPLE_RATIO*100:.0f}% from each bank...")
    samples_per_bank = TARGET_ROWS // len(datasets)
    sampled_rows = []

    for bank_id, df in datasets.items():
        n_samples = random.randint(
            int(MIN_SAMPLE_RATIO * len(df)),
            min(int(MAX_SAMPLE_RATIO * len(df)), samples_per_bank),
        )
        n_samples = min(n_samples, len(df))
        sample = df.sample(n=n_samples, random_state=RANDOM_SEED + bank_id)
        sample = sample.copy()
        sample["source_bank_id"] = bank_id  # Track origin
        sampled_rows.append(sample)

    # Combine
    combined = pd.concat(sampled_rows, ignore_index=True)
    print(f"  Combined: {len(combined):,} rows")

    # Trim or pad to target size
    if len(combined) > TARGET_ROWS:
        combined = combined.sample(n=TARGET_ROWS, random_state=RANDOM_SEED).reset_index(
            drop=True
        )
    elif len(combined) < TARGET_ROWS:
        # Duplicate some rows with augmentation
        needed = TARGET_ROWS - len(combined)
        additional = combined.sample(
            n=min(needed, len(combined)), random_state=RANDOM_SEED
        ).copy()
        combined = pd.concat([combined, additional], ignore_index=True)

    print(f"  Final size: {len(combined):,} rows")

    # Apply statistical perturbation
    print("\nApplying statistical perturbation...")
    combined = combined.copy()

    # Jitter numeric columns (amounts, values)
    numeric_cols = combined.select_dtypes(include=[np.number]).columns
    amount_like_cols = [
        c
        for c in numeric_cols
        if any(
            term in c.lower()
            for term in ["amount", "value", "price", "cost", "revenue"]
        )
    ]

    for col in amount_like_cols:
        if col in combined.columns:
            combined[col] = combined[col].apply(lambda x: jitter_amount(x) if pd.notna(x) else x)

    # Shift timestamps
    time_cols = [
        c
        for c in combined.columns
        if any(term in c.lower() for term in ["time", "date", "timestamp"])
    ]
    for col in time_cols:
        if col in combined.columns:
            combined[col] = combined[col].astype(str).apply(shift_timestamp)

    # Add noise to categorical (merchant, category, etc.)
    categorical_cols = combined.select_dtypes(include=["object"]).columns
    merchant_like_cols = [
        c
        for c in categorical_cols
        if any(term in c.lower() for term in ["merchant", "category", "type", "name"])
    ]
    for col in merchant_like_cols:
        if col in combined.columns and col != "source_bank_id":
            combined[col] = combined[col].astype(str).apply(add_noise_to_categorical)

    # Remove tracking column
    if "source_bank_id" in combined.columns:
        combined = combined.drop(columns=["source_bank_id"])

    print("  Augmentation complete")

    return combined


def main():
    """Generate synthetic bank 5 dataset."""
    print("=" * 60)
    print("Generating Synthetic Dataset for Bank 5")
    print("=" * 60)

    try:
        synthetic_df = mix_and_augment_datasets()
    except Exception as e:
        print(f"\n[ERROR] Failed to generate synthetic dataset: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Save
    output_dir = Path("datasets/processed/bank_5")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "bank_5_processed.csv"
    synthetic_df.to_csv(output_file, index=False)
    print(f"\n[OK] Saved synthetic dataset: {output_file}")

    # Save metadata
    metadata = {
        "bank_id": 5,
        "dataset_name": "Synthetic Mixed Dataset",
        "source": "Mixed from banks 1-4 with augmentation",
        "processed_rows": len(synthetic_df),
        "columns": list(synthetic_df.columns),
    }
    metadata_file = output_dir / "bank_5_metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))
    print(f"  Metadata: {metadata_file}")

    print("\n[OK] Synthetic dataset generation complete!")
    print("\nNext step: Run E2E pipeline: python datasets/run_e2e.py")


if __name__ == "__main__":
    main()



