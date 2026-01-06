from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Any

import pandas as pd
from charset_normalizer import from_bytes

from payscope_processing.tabular.headers import normalize_headers


@dataclass(frozen=True)
class TabularParseOutput:
    artifact_id: str
    source_object_key: str
    kind: str  # "csv" | "xlsx"
    tables: list[dict[str, Any]]


def parse_csv(
    *,
    artifact_id: str,
    object_key: str,
    file_path: str,
) -> TabularParseOutput:
    raw = _read_bytes(file_path, limit=256_000)
    encoding = _detect_encoding(raw)
    delimiter = _detect_delimiter(raw.decode(encoding, errors="replace"))
    header_row = _detect_header_row(raw.decode(encoding, errors="replace"), delimiter)

    df = pd.read_csv(
        file_path,
        encoding=encoding,
        sep=delimiter,
        engine="python",
        header=header_row,
        dtype=str,
        keep_default_na=False,
        on_bad_lines="skip",
    )

    orig_headers = [str(c) for c in df.columns.tolist()]
    norm_headers = normalize_headers(orig_headers)
    df.columns = norm_headers

    rows = []
    # pandas row index 0 corresponds to first data row after header; preserve original line number
    base_line = (header_row if header_row is not None else 0) + 2  # 1-based line numbers
    for i, r in enumerate(df.itertuples(index=False, name=None)):
        row_num = base_line + i
        rows.append(
            {
                "source_row_number": row_num,
                "values": {norm_headers[j]: (r[j] if r[j] is not None else "") for j in range(len(norm_headers))},
            }
        )

    return TabularParseOutput(
        artifact_id=artifact_id,
        source_object_key=object_key,
        kind="csv",
        tables=[
            {
                "sheet_name": None,
                "encoding": encoding,
                "delimiter": delimiter,
                "header_row": header_row,
                "columns_original": orig_headers,
                "columns_normalized": norm_headers,
                "rows": rows,
            }
        ],
    )


def parse_xlsx(
    *,
    artifact_id: str,
    object_key: str,
    file_path: str,
) -> TabularParseOutput:
    # Load all sheets as raw (header=None) first for header inference.
    sheets_raw = pd.read_excel(file_path, sheet_name=None, header=None, dtype=str, engine="openpyxl")

    tables: list[dict[str, Any]] = []

    for sheet_name, raw_df in sheets_raw.items():
        header_row = _detect_header_row_from_df(raw_df)
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=header_row,
            dtype=str,
            engine="openpyxl",
            keep_default_na=False,
        )

        orig_headers = [str(c) for c in df.columns.tolist()]
        norm_headers = normalize_headers(orig_headers)
        df.columns = norm_headers

        rows = []
        base_row = (header_row if header_row is not None else 0) + 2  # 1-based Excel row numbers
        for i, r in enumerate(df.itertuples(index=False, name=None)):
            src_row = base_row + i
            rows.append(
                {
                    "sheet_name": sheet_name,
                    "source_row_number": src_row,
                    "values": {norm_headers[j]: (r[j] if r[j] is not None else "") for j in range(len(norm_headers))},
                }
            )

        tables.append(
            {
                "sheet_name": sheet_name,
                "header_row": header_row,
                "columns_original": orig_headers,
                "columns_normalized": norm_headers,
                "rows": rows,
            }
        )

    return TabularParseOutput(
        artifact_id=artifact_id,
        source_object_key=object_key,
        kind="xlsx",
        tables=tables,
    )


def _read_bytes(path: str, *, limit: int) -> bytes:
    with open(path, "rb") as f:
        return f.read(limit)


def _detect_encoding(sample: bytes) -> str:
    best = from_bytes(sample).best()
    return (best.encoding if best and best.encoding else "utf-8")


def _detect_delimiter(text: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(text, delimiters=[",", "\t", ";", "|"])
        return dialect.delimiter
    except Exception:
        # Heuristic fallback
        counts = {d: text.count(d) for d in [",", "\t", ";", "|"]}
        return max(counts, key=counts.get) if counts else ","


def _detect_header_row(text: str, delimiter: str) -> int | None:
    lines = [ln for ln in text.splitlines()[:30] if ln.strip()]
    if not lines:
        return 0
    best_idx = 0
    best_score = -1.0
    for i, ln in enumerate(lines[:30]):
        parts = [p.strip() for p in ln.split(delimiter)]
        non_empty = sum(1 for p in parts if p)
        alpha = sum(1 for p in parts if any(c.isalpha() for c in p))
        uniq = len({p.lower() for p in parts if p})
        score = non_empty + 0.5 * alpha + 0.25 * uniq
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx


def _detect_header_row_from_df(df: pd.DataFrame) -> int | None:
    # Look at first 30 rows, score each row as "header-likeness"
    best_idx = 0
    best_score = -1.0
    nrows = min(30, len(df))
    if nrows == 0:
        return 0
    for i in range(nrows):
        row = df.iloc[i].tolist()
        parts = [("" if x is None else str(x)).strip() for x in row]
        non_empty = sum(1 for p in parts if p)
        alpha = sum(1 for p in parts if any(c.isalpha() for c in p))
        uniq = len({p.lower() for p in parts if p})
        score = non_empty + 0.5 * alpha + 0.25 * uniq
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx




