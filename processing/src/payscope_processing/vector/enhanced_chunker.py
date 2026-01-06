"""
Enhanced layout-aware chunking for reports.

Improves semantic chunking with layout understanding and report structure awareness.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from payscope_processing.contracts import IntermediateDocument
from payscope_processing.vector.chunker import ChunkingStrategy, SemanticChunker
from payscope_processing.vector.link_contract import VectorMetadata


class LayoutAwareChunker(SemanticChunker):
    """
    Enhanced chunker with layout-aware chunking.
    
    Uses layout understanding to create better semantic chunks.
    """

    def chunk_document(
        self,
        doc: IntermediateDocument,
        min_chunk_chars: int = 200,
        max_chunk_chars: int = 800,
        overlap_chars: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Chunk document with layout awareness.
        
        Enhanced version that respects:
        - Section boundaries
        - Table structures
        - LayoutLMv3 semantic tags
        """
        chunks = []

        # Group elements by semantic sections
        sections = self._group_by_sections(doc)
        
        for section_idx, section_elements in enumerate(sections):
            # Build section text
            section_text = "\n".join([el.text for el in section_elements if el.text.strip()])
            
            if len(section_text) < min_chunk_chars:
                # Merge with next section if too small
                if section_idx + 1 < len(sections):
                    next_section = sections[section_idx + 1]
                    next_text = "\n".join([el.text for el in next_section if el.text.strip()])
                    section_text = f"{section_text}\n{next_text}"
            
            # Split large sections intelligently
            if len(section_text) > max_chunk_chars:
                sub_chunks = self._split_large_section(section_text, max_chunk_chars, overlap_chars)
                chunks.extend(sub_chunks)
            else:
                chunks.append({
                    "text": section_text,
                    "elements": section_elements,
                    "section_index": section_idx,
                    "metadata": self._extract_section_metadata(section_elements),
                })
        
        return chunks

    def _group_by_sections(self, doc: IntermediateDocument) -> List[List]:
        """Group document elements by semantic sections."""
        sections = []
        current_section = []
        
        for el in doc.elements:
            # Detect section boundaries
            if self._is_section_header(el):
                if current_section:
                    sections.append(current_section)
                current_section = [el]
            else:
                current_section.append(el)
        
        if current_section:
            sections.append(current_section)
        
        return sections

    def _is_section_header(self, element) -> bool:
        """Detect if element is a section header."""
        # Check hierarchy metadata
        hierarchy = getattr(element, "hierarchy", {}) or {}
        
        # Check element type
        if element.element_type in ["title", "heading", "header"]:
            return True
        
        # Check text patterns
        text = element.text.strip()
        if text and len(text) < 100 and text.isupper():
            return True
        
        return False

    def _split_large_section(
        self,
        text: str,
        max_chars: int,
        overlap: int,
    ) -> List[Dict[str, Any]]:
        """Split large section into smaller chunks with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + max_chars, len(text))
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence boundary
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in ".!?\n":
                        end = i + 1
                        break
            
            chunk_text = text[start:end]
            chunks.append({
                "text": chunk_text,
                "start_offset": start,
                "end_offset": end,
            })
            
            start = end - overlap
        
        return chunks

    def _extract_section_metadata(self, elements: List) -> Dict[str, Any]:
        """Extract metadata from section elements."""
        metadata = {
            "element_count": len(elements),
            "has_tables": any(el.element_type == "table" for el in elements),
            "page_range": {
                "start": min(el.page_number for el in elements),
                "end": max(el.page_number for el in elements),
            },
        }
        
        # Extract layout tags if available
        layout_tags = []
        for el in elements:
            if hasattr(el, "hierarchy") and el.hierarchy:
                tag = el.hierarchy.get("category")
                if tag:
                    layout_tags.append(tag)
        
        if layout_tags:
            metadata["layout_tags"] = list(set(layout_tags))
        
        return metadata


def create_enhanced_chunker(
    strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
) -> LayoutAwareChunker:
    """Create enhanced layout-aware chunker."""
    return LayoutAwareChunker(strategy=strategy)



