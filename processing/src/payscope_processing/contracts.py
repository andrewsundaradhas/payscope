from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    page_width: float | None = None
    page_height: float | None = None
    unit: Literal["px", "pt", "unknown"] = "unknown"


class SourceFileRef(BaseModel):
    artifact_id: str
    object_key: str


class IntermediateElement(BaseModel):
    page_number: int
    element_type: str
    text: str
    bounding_box: BoundingBox | None = None
    confidence: float | None = None
    source_file: SourceFileRef
    hierarchy: dict = Field(default_factory=dict)


class IntermediateDocument(BaseModel):
    artifact_id: str
    elements: list[IntermediateElement]


class FieldPrediction(BaseModel):
    field_type: Literal["amount", "currency", "transaction_id", "date", "status"]
    confidence: float


class LayoutTaggedElement(BaseModel):
    element_id: str
    page_number: int
    text: str
    bounding_box: BoundingBox | None = None
    predictions: list[FieldPrediction]


class ColumnSemantics(BaseModel):
    column_id: str
    page_number: int
    bounding_box: BoundingBox | None = None
    predicted_field: FieldPrediction | None = None


class LayoutUnderstandingOutput(BaseModel):
    artifact_id: str
    elements: list[LayoutTaggedElement]
    columns: list[ColumnSemantics] = Field(default_factory=list)




