from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional
from src.core.document.engine import DocumentEngine

class DocumentService(DocumentEngine):
    """
    Refactored DocumentService that uses DocumentEngine.
    Maintained for backward compatibility and unified access.
    """
    def __init__(self) -> None:
        super().__init__()
        self.bank_founding_date = datetime.date(1937, 2, 10)

    def _html_to_pdf(self, html: str) -> bytes:
        return self.to_pdf(html)

    def _calculate_bank_years(self) -> int:
        today = datetime.date.today()
        years = today.year - self.bank_founding_date.year
        if (today.month, today.day) < (self.bank_founding_date.month, self.bank_founding_date.day):
            years -= 1
        return years

    def _render_template(self, template_name: str, **kwargs) -> str:
        # Inject legacy variables
        kwargs.setdefault("bank_years", self._calculate_bank_years())
        return self.render_doc(template_name, **kwargs)

    def _resolve_staff_profile(self, identifier: str) -> dict:
        return self.resolve_staff(identifier)

    # --- Unified Document Methods ---

    def generate_office_note(self, department: str, subject: str, intro_text: str, observations: str, recommendations: str, prepared_by: str = "Assistant", ref_no: str | None = None, date: str | None = None, signatories: list[str] | None = None, is_html: bool = False) -> str:
        initiator_profile = self._resolve_staff_profile(prepared_by)
        sig_profiles = [self._resolve_staff_profile(s) for s in (signatories or [])]
        
        context = {
            "department": department,
            "subject": subject,
            "intro_text": intro_text,
            "observations": observations,
            "recommendations": recommendations,
            "initiator": initiator_profile,
            "signatory_list": sig_profiles,
            "ref_no": ref_no or "RO/GEN/2026",
            "date": date or datetime.date.today().strftime("%d.%m.%Y"),
            "is_html": is_html
        }
        return self.render_doc("office_note.html", **context)

    def generate_pdf_note(self, *args, **kwargs) -> bytes:
        html = self.generate_office_note(*args, **kwargs)
        return self.to_pdf(html)

    def generate_anniversary_note(self, branch_name: str, branch_code: str, years: int, foundation_date: str | None = None, prepared_by: str | None = None) -> str:
        from .milestones import MilestoneGenerator
        gen = MilestoneGenerator(self)
        data = {
            "branch_name": branch_name,
            "branch_code": branch_code,
            "anniversary_year": years,
            "foundation_date": foundation_date,
            "prepared_by": prepared_by or "Regional Office",
            "date": datetime.date.today().strftime("%d.%m.%Y")
        }
        return gen.generate_anniversary_note_html(data)

    def generate_pdf_anniversary(self, *args, **kwargs) -> bytes:
        html = self.generate_anniversary_note(*args, **kwargs)
        return self.to_pdf(html)

    def generate_anniversary_poster_html(self, branch_name: str, years: int, open_date: str) -> str:
        template = self.env.get_template("anniversary_poster.html")
        return template.render(
            logo_url=self.org_data.get("bankLogo", ""),
            branch_name=branch_name,
            years=years,
            open_date=open_date,
            region_name=self.org_data.get("region_name", "Regional Office")
        )

    def generate_anniversary_poster_pdf(self, branch_name: str, years: int, open_date: str) -> bytes:
        html = self.generate_anniversary_poster_html(branch_name, years, open_date)
        return self.to_pdf(html)

    def generate_anniversary_poster_image(self, branch_name: str, years: int, open_date: str, theme: str = "executive") -> bytes:
        from .milestones import MilestoneGenerator
        gen = MilestoneGenerator(self)
        return gen.generate_branch_anniversary_image(branch_name, years, open_date, theme=theme)

    def generate_visiting_card_image(self, data: dict) -> list[bytes]:
        from .visiting_card_engine import VisitingCardEngine
        engine = VisitingCardEngine()
        return engine.render_card(data)

    def generate_daily_guardian_digest_html(self, date_str: str, sig_compile: str = "RO Guardian Desk", sig_review: str | list[str] = "Assistant General Manager", sig_approve: str = "Chief Regional Manager") -> str:
        from src.application.services.guardian_service import GuardianService
        g_svc = GuardianService()
        report_data = g_svc.compile_daily_report(date_str)
        
        # Resolve list vs string fallback
        sig_reviews = sig_review if isinstance(sig_review, list) else [sig_review]
        sig_review_fallback = " & ".join(sig_reviews)
        
        report_data.update({
            "sig_compile": sig_compile,
            "sig_review": sig_review_fallback,
            "sig_reviews": sig_reviews,
            "sig_approve": sig_approve
        })
        return self.render_doc("guardian_daily_digest.html", **report_data)

    def generate_daily_guardian_digest_pdf(self, date_str: str, sig_compile: str = "RO Guardian Desk", sig_review: str | list[str] = "Assistant General Manager", sig_approve: str = "Chief Regional Manager") -> bytes:
        html = self.generate_daily_guardian_digest_html(date_str, sig_compile, sig_review, sig_approve)
        return self.to_pdf(html)

    def generate_staff_milestone_image(self, staff_roll: str, milestone_type: str, theme: str = "executive") -> bytes:
        from .milestones import MilestoneGenerator
        gen = MilestoneGenerator(self)
        from src.infrastructure.persistence.master_repository import MasterRepository
        repo = MasterRepository()
        staff_rec = next((s for s in repo.get_by_category("STAFF") if s.code == staff_roll), None)
        branch_name = "REGIONAL OFFICE"
        if staff_rec:
            sol = (staff_rec.metadata or {}).get("sol")
            unit = next((u for u in repo.get_by_category("UNIT") if u.code == sol), None)
            if unit: branch_name = unit.name_en
            
        profile = self.resolve_staff(staff_roll)
        return gen.generate_staff_milestone_image(profile, milestone_type, branch_name, theme=theme)

    def generate_high_value_dd_html(self, data: dict) -> str:
        from src.infrastructure.persistence.master_repository import MasterRepository
        repo = MasterRepository()
        sol = data.get("branch_sol", "")
        branch_rec = next((u for u in repo.get_by_category("UNIT") if u.code == sol), None)
        issuing_branch = branch_rec.name_en if branch_rec else f"Branch (SOL: {sol})"

        context = data.copy()
        context.pop("branch_sol", None) 
        context.update({
            "current_date": datetime.date.today().strftime("%d.%m.%Y"),
            "branch_sol": sol,
            "issuing_branch": issuing_branch,
        })
        return self.render_doc("high_value_dd.html", **context)

    def generate_high_value_dd_pdf(self, data: dict) -> bytes:
        html = self.generate_high_value_dd_html(data)
        return self.to_pdf(html)

    def _prepare_circular_data(self, circular_data: dict) -> dict:
        data = circular_data.copy()
        if "author" in data:
            data["sig"] = self.resolve_staff(data["author"])
        else:
            data["sig"] = {"name": "Manager", "roll": "12345", "name_ta": "மேலாளர்", "name_hi": "प्रबंधक", "desig_en": "Manager", "desig_ta": "மேலாளர்", "desig_hi": "प्रबंधक"}
        data["is_html"] = True # Helps formatting in HTML preview vs PDF
        return data

    def generate_circular_html(self, circular_data: dict) -> str:
        from .operational import OperationalGenerator
        gen = OperationalGenerator(self)
        data = self._prepare_circular_data(circular_data)
        return gen.generate_circular_html(data)

    def generate_circular_pdf(self, circular_data: dict) -> bytes:
        from .operational import OperationalGenerator
        gen = OperationalGenerator(self)
        data = self._prepare_circular_data(circular_data)
        data["is_html"] = False
        return gen.generate_circular_pdf(data)

    def generate_performance_appreciation(self, performance: dict) -> bytes:
        from .performance import PerformanceGenerator
        gen = PerformanceGenerator(self)
        return gen.generate_appreciation(performance)

    def generate_explanation_letter(self, performance: dict) -> bytes:
        from .performance import PerformanceGenerator
        gen = PerformanceGenerator(self)
        return gen.generate_explanation(performance)

    def generate_budget_communication(self, payload: dict) -> bytes:
        from .performance import PerformanceGenerator
        gen = PerformanceGenerator(self)
        return gen.generate_budget_communication(payload)

    def generate_custom_letter_pdf(self, *args, **kwargs) -> bytes:
        from .operational import OperationalGenerator
        gen = OperationalGenerator(self)
        data = kwargs.copy()
        sig_roll = data.get("signatory_roll")
        if sig_roll:
            data["signatory"] = self.resolve_staff(sig_roll)
        return gen.generate_custom_letter(data)

    def generate_appreciation_certificate_pdf(self, recipient_roll: str, reason: str, signatory_roll: str, date: str = None) -> bytes:
        from .milestones import MilestoneGenerator
        gen = MilestoneGenerator(self)
        recipient = self.resolve_staff(recipient_roll)
        signatory = self.resolve_staff(signatory_roll)
        return gen.generate_appreciation_certificate(recipient, reason, signatory, date or datetime.date.today().strftime("%d.%m.%Y"))

    def generate_milestones_pdf(self, milestones: list, summary: list, report_date: str) -> bytes:
        """Generates a professional regional milestones inventory report."""
        html = self.render_doc(
            "milestones_report.html",
            milestones=milestones,
            summary=summary,
            report_date=report_date
        )
        return self.to_pdf(html)

    def generate_milestone_appreciation(self, breakthrough: dict, signatory: dict) -> bytes:
        """Generates a formal appreciation letter for business milestones."""
        html = self.render_doc(
            "appreciation_letter.html",
            branch_name=breakthrough["branch_name"],
            sol=breakthrough["sol"],
            milestone=breakthrough["milestone"],
            parameter=breakthrough["parameter"],
            achievement_date=breakthrough["date"].strftime("%d.%m.%Y"),
            month_year=breakthrough["date"].strftime("%B %Y"),
            signatory=signatory
        )
        return self.to_pdf(html)

    def generate_branch_visit_report(self, month: int, year: int, visits: list, signatory_roll: str | None = None) -> bytes:
        """Generates the consolidated branch visit report PDF."""
        import datetime
        month_name = datetime.date(year, month, 1).strftime("%B")
        signatory = self.resolve_staff(signatory_roll) if signatory_roll else None
        
        html = self.render_doc(
            "branch_visit_report.html",
            month_name=month_name,
            year=year,
            visits=visits,
            signatory=signatory
        )
        return self.to_pdf(html)

    def generate_visit_observation_letter(self, visit: Any, signatory_roll: str | None = None) -> bytes:
        """Generates individual branch visit observation letters using resolved signatory details."""
        from .operational import OperationalGenerator
        gen = OperationalGenerator(self)
        signatory = self.resolve_staff(signatory_roll) if signatory_roll else None
        if not signatory:
            signatory = {
                "name": "CHANDRA KUMAR P",
                "name_hi": "चंद्र कुमार पी",
                "name_ta": "சந்திர குமார் பி",
                "roll": "36614",
                "desig_en": "SENIOR REGIONAL MANAGER",
                "desig_hi": "वरिष्ठ क्षेत्रीय प्रबंधक",
                "desig_ta": "முதன்மை மண்டல மேலாளர்"
            }
        
        data = {
            "branch_name": visit.branch_name,
            "sol": visit.sol,
            "visitor_name": visit.visitor_name,
            "visit_date": visit.visit_date,
            "observations": visit.observations,
            "advice": visit.advice_to_branch,
            "signatory": signatory
        }
        return gen.generate_visit_observation(data)

    def generate_wizard_pdf(self, wizard_type: str, data: dict, submitted_by: str, subject: str = None, ref: str = None) -> bytes:
        """Generates a PDF report for any wizard submission."""
        if wizard_type == "office_note":
            prep_name = data.get('signatorySnapshot', {}).get('preparer', {}).get('name', submitted_by)
            rev_list = data.get('signatorySnapshot', {}).get('reviewers', [])
            sigs = [s.get('name') for s in rev_list] if isinstance(rev_list, list) else []
            
            # Extract distinct text keys if available, otherwise parse legacy combined details
            intro = data.get('intro', '')
            obs = data.get('obs', '')
            recs = data.get('recs', '')
            
            if not (intro or obs or recs):
                details = data.get('details', '')
                if "<h3>Introduction</h3>" in details and "<h3>Observations</h3>" in details and "<h3>Recommendations</h3>" in details:
                    try:
                        p1 = details.split("<h3>Introduction</h3>", 1)[1]
                        intro_part, p2 = p1.split("<h3>Observations</h3>", 1)
                        obs_part, recs_part = p2.split("<h3>Recommendations</h3>", 1)
                        intro = intro_part.strip()
                        obs = obs_part.strip()
                        recs = recs_part.strip()
                    except Exception:
                        obs = details
                else:
                    obs = details
                
            return self.generate_pdf_note(
                department=data.get('deptName', 'PLAN'),
                subject=subject or "Office Note",
                intro_text=intro,
                observations=obs,
                recommendations=recs,
                prepared_by=prep_name,
                ref_no=ref,
                date=data.get('noteDate'),
                signatories=sigs,
                is_html=True
            )

        if wizard_type == "circular_drafter":
            return self.generate_circular_pdf(data)

        title_map = {
            "broken_interest": "Broken Period Interest Calculation",
            "rbi_proforma": "RBI Proforma Reporting",
            "expense_approval": "Administrative Expense Approval",
            "gl_activation": "GL Head Activation Request",
            "high_value_dd": "High Value DD Reporting",
            "micr_request": "MICR/Cheque Book Request",
            "proforma_branch": "Proforma Branch Code Capture",
            "reversal_charges": "Reversal of Charges / Waiver Request"
        }
        
        template = "wizard_generic.html"
        if wizard_type == "broken_interest":
            template = "wizard_broken_interest.html"
            
        html = self._render_template(
            template,
            title=subject or title_map.get(wizard_type, wizard_type.replace('_', ' ').title()),
            data=data,
            submitted_by=submitted_by,
            reference_no=ref,
            date=datetime.date.today().strftime("%d.%m.%Y"),
            **data
        )
        return self.to_pdf(html)


