from __future__ import annotations
from typing import Dict, Any
from src.core.document.engine import DocumentEngine

class StatutoryGenerator:
    """Generates statutory returns and regulatory documents."""
    def __init__(self, engine: DocumentEngine | None = None) -> None:
        self.engine = engine or DocumentEngine()

    def generate_dicgc_return(self, data: Dict[str, Any]) -> bytes:
        html = self.engine.render_doc(
            "dicgc_return.html",
            **data
        )
        return self.engine.to_pdf(html)

    def generate_dicgc_di01(self, data: Dict[str, Any]) -> bytes:
        html = self.engine.render_doc(
            "dicgc_form_di01.html",
            **data
        )
        return self.engine.to_pdf(html)

    def generate_wizard_generic(self, data: Dict[str, Any]) -> bytes:
        html = self.engine.render_doc(
            "wizard_generic.html",
            **data
        )
        return self.engine.to_pdf(html)
