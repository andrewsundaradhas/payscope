from __future__ import annotations

import math
import os
import re
import uuid
from dataclasses import dataclass

import torch
from transformers import LayoutLMv3Model, LayoutLMv3Processor

from payscope_processing.contracts import (
    BoundingBox,
    ColumnSemantics,
    FieldPrediction,
    IntermediateDocument,
    LayoutTaggedElement,
    LayoutUnderstandingOutput,
)


_AMOUNT_RE = re.compile(r"^[\(\-]?\$?\s*\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?\)?$")
_CURRENCY_RE = re.compile(r"\b(usd|eur|gbp|cad|aud|jpy)\b", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b")
_TXN_RE = re.compile(r"\b(txn|transaction)\b", re.IGNORECASE)
_STATUS_RE = re.compile(r"\b(approved|declined|paid|unpaid|settled|pending|reversed)\b", re.IGNORECASE)


@dataclass(frozen=True)
class _Anchors:
    amount: list[str]
    currency: list[str]
    transaction_id: list[str]
    date: list[str]
    status: list[str]


ANCHORS = _Anchors(
    amount=["amount", "total", "net amount", "gross", "$ 123.45", "fee"],
    currency=["currency", "usd", "eur", "gbp"],
    transaction_id=["transaction id", "txn id", "reference", "auth code"],
    date=["date", "settlement date", "posting date", "2025-12-31"],
    status=["status", "approved", "declined", "pending", "settled"],
)


class LayoutLMv3Tagger:
    """
    Uses LayoutLMv3 embeddings (layout + text jointly) to produce schema-agnostic field predictions.

    Design choice (brief):
      - We avoid assuming a supervised dataset. Instead, we compute deterministic similarities to
        anchor phrases for the required financial field types and combine them with regex heuristics.
    """

    def __init__(self, model_name: str = "microsoft/layoutlmv3-base", device: str | None = None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)

        hf_home = os.getenv("HF_HOME")
        if hf_home:
            os.environ["HF_HOME"] = hf_home

        self.processor = LayoutLMv3Processor.from_pretrained(model_name, apply_ocr=False)
        self.model = LayoutLMv3Model.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

        # Precompute anchor embeddings
        self._anchor_vecs = self._embed_anchors()

    @torch.no_grad()
    def tag(self, doc: IntermediateDocument) -> LayoutUnderstandingOutput:
        elements_out: list[LayoutTaggedElement] = []

        # Compute element embeddings page-by-page (LayoutLM expects page coordinate normalization).
        by_page: dict[int, list] = {}
        for el in doc.elements:
            by_page.setdefault(el.page_number, []).append(el)

        # For column semantics: assign column groups by x-center clustering (simple deterministic).
        columns_out: list[ColumnSemantics] = []

        for page_number, els in by_page.items():
            # Prepare per-element embedding based on text + bbox.
            page_dim = _page_dim(els)

            el_vecs: dict[str, torch.Tensor] = {}
            for el in els:
                el_id = f"{page_number}:{uuid.uuid4().hex[:8]}"
                vec = self._embed_element(el.text, el.bounding_box, page_dim)
                el_vecs[el_id] = vec

                preds = self._predict_fields(el.text, vec, base_conf=el.confidence)
                elements_out.append(
                    LayoutTaggedElement(
                        element_id=el_id,
                        page_number=page_number,
                        text=el.text,
                        bounding_box=el.bounding_box,
                        predictions=preds,
                    )
                )

            # Column grouping + semantics (layout-driven)
            col_assignments = _assign_columns(els, page_dim)
            for col_id, bbox, member_idxs in col_assignments:
                # aggregate predictions from members
                agg: dict[str, float] = {"amount": 0, "currency": 0, "transaction_id": 0, "date": 0, "status": 0}
                for mi in member_idxs:
                    text = els[mi].text
                    vec = self._embed_element(text, els[mi].bounding_box, page_dim)
                    preds = self._predict_fields(text, vec, base_conf=els[mi].confidence)
                    for p in preds:
                        agg[p.field_type] += p.confidence

                best = max(agg.items(), key=lambda kv: kv[1])
                best_pred = FieldPrediction(field_type=best[0], confidence=_clamp01(best[1] / max(1, len(member_idxs))))
                columns_out.append(
                    ColumnSemantics(
                        column_id=col_id,
                        page_number=page_number,
                        bounding_box=bbox,
                        predicted_field=best_pred,
                    )
                )

        return LayoutUnderstandingOutput(artifact_id=doc.artifact_id, elements=elements_out, columns=columns_out)

    def _embed_anchors(self) -> dict[str, torch.Tensor]:
        out: dict[str, torch.Tensor] = {}
        for field, phrases in ANCHORS.__dict__.items():
            vecs = []
            for p in phrases:
                vecs.append(self._embed_text_only(p))
            out[field] = torch.stack(vecs, dim=0).mean(dim=0)
        return out

    @torch.no_grad()
    def _embed_text_only(self, text: str) -> torch.Tensor:
        enc = self.processor(text=[text], boxes=[[ [0,0,1000,1000] ]], return_tensors="pt", truncation=True)
        enc = {k: v.to(self.device) for k, v in enc.items()}
        out = self.model(**enc)
        # average last hidden state over tokens
        vec = out.last_hidden_state.mean(dim=1).squeeze(0)
        return vec / (vec.norm(p=2) + 1e-8)

    @torch.no_grad()
    def _embed_element(self, text: str, bbox: BoundingBox | None, page_dim: tuple[float, float]) -> torch.Tensor:
        w, h = page_dim
        box = _to_layoutlm_box(bbox, w=w, h=h)
        enc = self.processor(text=[text], boxes=[[box]], return_tensors="pt", truncation=True)
        enc = {k: v.to(self.device) for k, v in enc.items()}
        out = self.model(**enc)
        vec = out.last_hidden_state.mean(dim=1).squeeze(0)
        return vec / (vec.norm(p=2) + 1e-8)

    def _predict_fields(self, text: str, vec: torch.Tensor, base_conf: float | None) -> list[FieldPrediction]:
        # Similarity to anchors
        sims = {}
        for k, a in self._anchor_vecs.items():
            sims[k] = float(torch.dot(vec, a).clamp(-1, 1).item())
        # Softmax over similarities
        exps = {k: math.exp(v * 3.0) for k, v in sims.items()}
        z = sum(exps.values()) or 1.0
        probs = {k: exps[k] / z for k in exps}

        # Regex heuristics (deterministic)
        heur = {
            "amount": 1.0 if _AMOUNT_RE.match(text.strip()) else (0.6 if "$" in text else 0.0),
            "currency": 1.0 if _CURRENCY_RE.search(text) else 0.0,
            "transaction_id": 0.8 if _TXN_RE.search(text) else 0.0,
            "date": 1.0 if _DATE_RE.search(text) else 0.0,
            "status": 1.0 if _STATUS_RE.search(text) else 0.0,
        }

        base = _clamp01(base_conf if base_conf is not None else 1.0)

        preds: list[FieldPrediction] = []
        for ft in ["amount", "currency", "transaction_id", "date", "status"]:
            conf = probs[ft] * (0.5 + 0.5 * heur[ft]) * base
            preds.append(FieldPrediction(field_type=ft, confidence=_clamp01(conf)))

        # Return top-k (keep schema-agnostic but compact)
        preds.sort(key=lambda p: p.confidence, reverse=True)
        return [p for p in preds if p.confidence >= 0.15][:3]


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def _page_dim(els) -> tuple[float, float]:
    # Prefer explicit page dims from any bbox, else fallback to 1000x1000.
    for e in els:
        b = e.bounding_box
        if b and b.page_width and b.page_height:
            return float(b.page_width), float(b.page_height)
    return 1000.0, 1000.0


def _to_layoutlm_box(b: BoundingBox | None, *, w: float, h: float) -> list[int]:
    if b is None or w <= 0 or h <= 0:
        return [0, 0, 1000, 1000]
    x1 = int(max(0, min(1000, round((b.x1 / w) * 1000))))
    y1 = int(max(0, min(1000, round((b.y1 / h) * 1000))))
    x2 = int(max(0, min(1000, round((b.x2 / w) * 1000))))
    y2 = int(max(0, min(1000, round((b.y2 / h) * 1000))))
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    return [x1, y1, x2, y2]


def _assign_columns(els, page_dim: tuple[float, float]) -> list[tuple[str, BoundingBox, list[int]]]:
    """
    Deterministic column inference using x-centers. This is schema-agnostic and purely layout-driven.
    """
    w, h = page_dim
    xs = []
    idxs = []
    for i, e in enumerate(els):
        b = e.bounding_box
        if b is None:
            continue
        cx = (b.x1 + b.x2) / 2.0
        xs.append(cx)
        idxs.append(i)
    if not xs:
        return []

    # Simple binning into up to 6 columns using quantiles.
    cols = min(6, max(1, len(xs) // 20))
    xs_sorted = sorted(xs)
    cuts = [xs_sorted[int(len(xs_sorted) * q / cols)] for q in range(1, cols)]

    def col_of(cx: float) -> int:
        for j, c in enumerate(cuts):
            if cx <= c:
                return j
        return len(cuts)

    groups: dict[int, list[int]] = {}
    for cx, i in zip(xs, idxs):
        groups.setdefault(col_of(cx), []).append(i)

    out = []
    for c, members in sorted(groups.items()):
        # bbox union
        x1 = min(els[i].bounding_box.x1 for i in members if els[i].bounding_box)
        y1 = min(els[i].bounding_box.y1 for i in members if els[i].bounding_box)
        x2 = max(els[i].bounding_box.x2 for i in members if els[i].bounding_box)
        y2 = max(els[i].bounding_box.y2 for i in members if els[i].bounding_box)
        bbox = BoundingBox(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2), page_width=w, page_height=h, unit="px")
        out.append((f"col_{c+1}", bbox, members))
    return out




