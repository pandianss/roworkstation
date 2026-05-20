from __future__ import annotations
from typing import Dict, List, Any
from src.core.document.engine import DocumentEngine

class OperationalGenerator:
    """Generates day-to-day operational documents."""
    def __init__(self, engine: DocumentEngine | None = None) -> None:
        self.engine = engine or DocumentEngine()

    def generate_office_note(self, data: Dict[str, Any]) -> bytes:
        html = self.engine.render_doc(
            "office_note.html",
            **data
        )
        return self.engine.to_pdf(html)

    def generate_circular_html(self, data: Dict[str, Any]) -> str:
        return self.engine.render_doc(
            "circular.html",
            **data
        )

    def generate_circular_pdf(self, data: Dict[str, Any]) -> bytes:
        html = self.generate_circular_html(data)
        return self.engine.to_pdf(html)

    def generate_visit_observation(self, data: Dict[str, Any]) -> bytes:
        html = self.engine.render_doc(
            "visit_observation_letter.html",
            **data
        )
        return self.engine.to_pdf(html)

    def generate_custom_letter(self, data: Dict[str, Any]) -> bytes:
        html = self.engine.render_doc(
            "custom_letter.html",
            **data
        )
        return self.engine.to_pdf(html)
