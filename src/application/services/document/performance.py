from __future__ import annotations
from typing import Dict, List, Any
from src.core.document.engine import DocumentEngine

class PerformanceGenerator:
    """Generates budget communications and performance letters."""
    def __init__(self, engine: DocumentEngine | None = None) -> None:
        self.engine = engine or DocumentEngine()

    def generate_appreciation(self, performance: Dict[str, Any]) -> bytes:
        html = self.engine.render_doc(
            "performance_appreciation.html",
            branch_name=performance["branch_name"],
            sol=performance["sol"],
            branch_head=performance.get("branch_head"),
            achievements=performance["achievements"],
            group_name=performance.get("group_name", "Budget"),
            month_year=performance["date"].strftime("%B %Y"),
            signatory=performance.get("signatory"),
            ref_no=performance.get("ref_no"),
            date=performance.get("date").strftime("%d.%m.%Y")
        )
        return self.engine.to_pdf(html)

    def generate_explanation(self, performance: Dict[str, Any]) -> bytes:
        html = self.engine.render_doc(
            "explanation_letter.html",
            branch_name=performance["branch_name"],
            sol=performance["sol"],
            branch_head=performance.get("branch_head"),
            declines=performance["declines"],
            group_name=performance.get("group_name", "Budget"),
            month_year=performance["date"].strftime("%B %Y"),
            signatory=performance.get("signatory"),
            ref_no=performance.get("ref_no"),
            date=performance.get("date").strftime("%d.%m.%Y")
        )
        return self.engine.to_pdf(html)

    def generate_budget_communication(self, payload: Dict[str, Any]) -> bytes:
        html = self.engine.render_doc(
            "budget_communication.html",
            branch_name=payload["branch_name"],
            sol=payload["sol"],
            branch_head=payload.get("branch_head"),
            budget_groups=payload["budget_groups"],
            months=payload.get("months", []),
            fy_range=payload.get("fy_range", "2026-27"),
            signatory=payload["signatory"],
            ref_no=payload.get("ref_no"),
            date=payload.get("date")
        )
        return self.engine.to_pdf(html)
