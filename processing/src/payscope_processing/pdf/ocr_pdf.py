from __future__ import annotations

import math
from dataclasses import dataclass

import fitz  # PyMuPDF
from paddleocr import PaddleOCR

from payscope_processing.contracts import BoundingBox, IntermediateElement, IntermediateDocument, SourceFileRef


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float
    bbox: BoundingBox


_OCR: PaddleOCR | None = None


def _get_ocr() -> PaddleOCR:
    global _OCR
    if _OCR is None:
        # Deterministic baseline: English model. Language detection is done post-OCR.
        _OCR = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _OCR


def parse_scanned_pdf_via_ocr(
    *,
    artifact_id: str,
    object_key: str,
    file_path: str,
) -> IntermediateDocument:
    """
    Scanned PDF parsing via PaddleOCR.

    Output elements include bounding boxes (pixel coordinates), confidence, and page dimensions.
    """
    doc = fitz.open(file_path)
    src = SourceFileRef(artifact_id=artifact_id, object_key=object_key)
    ocr = _get_ocr()

    out: list[IntermediateElement] = []

    for page_idx in range(len(doc)):
        page = doc.load_page(page_idx)
        pix = page.get_pixmap(dpi=200, alpha=False)
        page_w = float(pix.width)
        page_h = float(pix.height)

        img_bytes = pix.tobytes("png")
        result = ocr.ocr(img_bytes, cls=True)
        lines = _normalize_paddle_result(result, page_w=page_w, page_h=page_h)

        # Preserve reading order: top-to-bottom, left-to-right by bbox.
        lines.sort(key=lambda l: (l.bbox.y1, l.bbox.x1))

        for li, line in enumerate(lines):
            out.append(
                IntermediateElement(
                    page_number=page_idx + 1,
                    element_type="text",
                    text=line.text,
                    bounding_box=line.bbox,
                    confidence=line.confidence,
                    source_file=src,
                    hierarchy={"line_index": li, "ocr_engine": "paddleocr"},
                )
            )

    return IntermediateDocument(artifact_id=artifact_id, elements=out)


def _normalize_paddle_result(result, *, page_w: float, page_h: float) -> list[OcrLine]:
    lines: list[OcrLine] = []
    if not result:
        return lines

    # PaddleOCR returns: [ [ [ [x,y]...4 ], (text, conf) ], ... ]
    for item in result[0] if isinstance(result, list) and len(result) == 1 and isinstance(result[0], list) else result:
        try:
            pts = item[0]
            text, conf = item[1]
            xs = [float(p[0]) for p in pts]
            ys = [float(p[1]) for p in pts]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
            # Clamp to page bounds
            x1 = max(0.0, min(page_w, x1))
            x2 = max(0.0, min(page_w, x2))
            y1 = max(0.0, min(page_h, y1))
            y2 = max(0.0, min(page_h, y2))
            conf_f = float(conf)
            if math.isnan(conf_f) or conf_f < 0:
                conf_f = 0.0
            if conf_f > 1:
                conf_f = 1.0
            bbox = BoundingBox(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                page_width=page_w,
                page_height=page_h,
                unit="px",
            )
            t = str(text).strip()
            if t:
                lines.append(OcrLine(text=t, confidence=conf_f, bbox=bbox))
        except Exception:
            continue
    return lines




