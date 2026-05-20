from __future__ import annotations
from typing import Dict, Any
from io import BytesIO
from src.core.document.engine import DocumentEngine
from src.application.services.document.celebration_engine import CelebrationEngine


class MilestoneGenerator:
    """Generates celebratory and milestone-based documents."""
    def __init__(self, engine: DocumentEngine | None = None) -> None:
        self.engine = engine or DocumentEngine()
        self.image_engine = CelebrationEngine()

    def generate_anniversary_note_html(self, data: Dict[str, Any]) -> str:
        return self.engine.render_doc(
            "anniversary_note.html",
            **data
        )

    def generate_anniversary_note_pdf(self, data: Dict[str, Any]) -> bytes:
        html = self.generate_anniversary_note_html(data)
        return self.engine.to_pdf(html)

    def generate_anniversary_note(self, data: Dict[str, Any]) -> bytes:
        """Backward-compatible PDF API used by older document-centre code."""
        return self.generate_anniversary_note_pdf(data)

    def generate_staff_milestone_image(self, profile: Dict[str, Any], milestone_type: str, branch_name: str, theme: str = "executive") -> bytes:
        """Generates a high-resolution PNG image using the new PIL engine."""
        data = {
            "milestone_type": milestone_type.upper(),
            "name_en": profile["name"],
            "designation": profile.get("desig_en", ""),
            "branch_name": branch_name
        }
        image = self.image_engine.render_poster(data, theme_key=theme)
        buf = BytesIO()
        image.save(buf, format="PNG", quality=95)
        return buf.getvalue()

    def generate_branch_anniversary_image(self, branch_name: str, years: int, open_date: str, theme: str = "executive") -> bytes:
        """Generates a high-resolution branch anniversary PNG image."""
        data = {
            "branch_name": branch_name,
            "years": years,
            "open_date": open_date,
            "region_name": self.engine.org_data.get("region_name", "Regional Office")
        }
        image = self.image_engine.render_anniversary(data, theme_key=theme)
        buf = BytesIO()
        image.save(buf, format="PNG", quality=95)
        return buf.getvalue()

    def generate_staff_milestone(self, profile: Dict[str, Any], milestone_type: str, branch_name: str) -> bytes:
        """Backward-compatible API that now returns the PIL-generated PNG poster."""
        return self.generate_staff_milestone_image(profile, milestone_type, branch_name)

    def generate_appreciation_certificate(self, recipient: Dict[str, Any], reason: str, signatory: Dict[str, Any], date: str) -> bytes:
        html = self.engine.render_doc(
            "appreciation_certificate.html",
            recipient=recipient,
            reason=reason,
            signatory=signatory,
            date=date,
            ref_no=f"RO/DGL/CERT/{recipient['roll']}/{date[-4:]}"
        )
        return self.engine.to_pdf(html)
