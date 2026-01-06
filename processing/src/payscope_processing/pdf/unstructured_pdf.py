from __future__ import annotations

from typing import Any

from unstructured.partition.pdf import partition_pdf

from payscope_processing.contracts import BoundingBox, IntermediateElement, IntermediateDocument, SourceFileRef


def parse_digital_pdf(
    *,
    artifact_id: str,
    object_key: str,
    file_path: str,
) -> IntermediateDocument:
    """
    Digital PDF parsing via Unstructured.

    - Preserves reading order (list order from Unstructured)
    - Extracts tables + headers/footers where available
    - Emits best-effort coordinates when present in element.metadata
    """
    elements = partition_pdf(
        filename=file_path,
        infer_table_structure=True,
        include_page_breaks=False,
        strategy="fast",
    )

    out: list[IntermediateElement] = []
    src = SourceFileRef(artifact_id=artifact_id, object_key=object_key)

    for idx, el in enumerate(elements):
        md: Any = getattr(el, "metadata", None)
        page_number = int(getattr(md, "page_number", 1) or 1)
        category = getattr(el, "category", None) or el.__class__.__name__
        text = (getattr(el, "text", None) or "").strip()

        bbox = None
        coords = getattr(md, "coordinates", None)
        # Unstructured coordinates are not guaranteed; when present, normalize to a simple bbox.
        if coords and getattr(coords, "points", None):
            pts = coords.points
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            bbox = BoundingBox(
                x1=float(min(xs)),
                y1=float(min(ys)),
                x2=float(max(xs)),
                y2=float(max(ys)),
                unit="pt",
            )

        hierarchy: dict[str, Any] = {
            "element_index": idx,
            "unstructured_type": el.__class__.__name__,
        }
        if md:
            for k in ["parent_id", "category_depth", "text_as_html", "filename"]:
                v = getattr(md, k, None)
                if v is not None:
                    hierarchy[k] = v

        out.append(
            IntermediateElement(
                page_number=page_number,
                element_type=str(category).lower(),
                text=text,
                bounding_box=bbox,
                confidence=None,
                source_file=src,
                hierarchy=hierarchy,
            )
        )

    return IntermediateDocument(artifact_id=artifact_id, elements=out)




