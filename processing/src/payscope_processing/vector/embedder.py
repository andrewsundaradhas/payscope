from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, List

import torch
from sentence_transformers import SentenceTransformer


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str
    device: str | None = None  # "cpu" | "cuda"


class Embedder:
    """
    Production-grade embedding wrapper.

    Model choice: default "BAAI/bge-base-en-v1.5"
      - strong retrieval performance on English + financial text
      - 768 dims (balanced latency/cost)
      - open-source, offline-capable (no remote dependency)
    """

    def __init__(self, cfg: EmbeddingConfig):
        device = cfg.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer(cfg.model_name, device=device)

    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        return [vec.tolist() for vec in self.model.encode(list(texts), normalize_embeddings=True, convert_to_numpy=False)]




