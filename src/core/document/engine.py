from __future__ import annotations
import io
import datetime
import base64
import subprocess
import tempfile
import os
import time
import shutil
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader

from src.core.paths import project_path
from src.core.registry.parameter_service import ParameterRegistry

logger = logging.getLogger(__name__)

class DocumentEngine:
    """
    Unified engine for HTML-to-PDF generation.
    Handles templates, assets, and the headless browser interface.
    """
    def __init__(self, template_subdir: str = "") -> None:
        self.registry = ParameterRegistry()
        self.template_dir = project_path("src", "infrastructure", "templates")
        if template_subdir:
            self.template_dir = self.template_dir / template_subdir
            
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        self._add_filters()
        
        self.assets_dir = project_path("src", "assets")
        self.fonts_dir = project_path("data", "fonts")
        self.org_data = self._load_org_data()

    def _add_filters(self):
        """Adds common Jinja2 filters for financial data with Indian formatting."""
        # Manual implementation for robustness
        
        def format_inr(value):
            try:
                if value is None: return "0.00"
                # Use robust formatting logic
                num = float(str(value).replace(',', '').replace('₹', '').replace(' ', '').strip() or 0)
                is_neg = num < 0
                num = abs(num)
                
                s = "{:.2f}".format(num)
                parts = s.split(".")
                int_part, dec_part = parts[0], parts[1]
                
                res = ""
                if len(int_part) <= 3:
                    res = int_part
                else:
                    res = int_part[-3:]
                    rem = int_part[:-3]
                    while len(rem) > 2:
                        res = rem[-2:] + "," + res
                        rem = rem[:-2]
                    if rem: res = rem + "," + res
                
                final = res + "." + dec_part
                return "-" + final if is_neg else final
            except (TypeError, ValueError):
                return str(value)
        
        def format_inr_k(value):
            try:
                if value is None: return "0"
                num = float(str(value).replace(',', '').replace('₹', '').replace(' ', '').strip() or 0)
                is_neg = num < 0
                num = abs(num)
                
                int_part = str(int(num))
                res = ""
                if len(int_part) <= 3:
                    res = int_part
                else:
                    res = int_part[-3:]
                    rem = int_part[:-3]
                    while len(rem) > 2:
                        res = rem[-2:] + "," + res
                        rem = rem[:-2]
                    if rem: res = rem + "," + res
                
                return "-" + res if is_neg else res
            except (TypeError, ValueError):
                return str(value)

        def format_date(value, fmt="%d.%m.%Y"):
            if not value: return ""
            if isinstance(value, str):
                try:
                    # Attempt to parse common formats
                    for f in ["%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]:
                        try:
                            value = datetime.datetime.strptime(value, f)
                            break
                        except ValueError:
                            continue
                except (TypeError, ValueError):
                    return value
            try:
                return value.strftime(fmt)
            except AttributeError:
                return str(value)

        self.env.filters['format_inr'] = format_inr
        self.env.filters['format_inr_k'] = format_inr_k
        self.env.filters['format_date'] = format_date

    def _load_org_data(self) -> Dict[str, Any]:
        """Loads organizational metadata from registry with master data overrides."""
        org = self.registry.get_org_info()
        contact = self.registry.get_contact_info()
        
        ro_address_en = contact["address"]["en"]
        ro_address_hi = contact["address"]["hi"]
        ro_address_ta = contact["address"]["ta"]
        
        try:
            from src.infrastructure.persistence.master_repository import MasterRepository
            repo = MasterRepository()
            recs = repo.get_by_category('UNIT')
            ro_rec = next((r for r in recs if r.code == '3933'), None)
            if ro_rec and ro_rec.metadata:
                m = ro_rec.metadata
                addr_en = f"{m.get('address2_en', '')}, {m.get('address3_en', '')}".strip(", ")
                addr_hi = f"{m.get('address2_hi', '')}, {m.get('address3_hi', '')}".strip(", ")
                addr_ta = f"{m.get('address2_ta', '')}, {m.get('address3_ta', '')}".strip(", ")
                
                if addr_en:
                    ro_address_en = addr_en
                if addr_hi:
                    ro_address_hi = addr_hi
                if addr_ta:
                    ro_address_ta = addr_ta
        except Exception as e:
            logger.warning("Failed to fetch RO address from master repository: %s", e)

        # Format address with breaks
        def format_address(addr, marker):
            if not addr: return ""
            addr = str(addr).replace("<br/>", "").replace("<br>", "").replace("\n", " ").strip()
            addr = ", ".join([p.strip() for p in addr.split(",") if p.strip()])
            if marker in addr:
                parts = addr.split(marker, 1)
                return f"{parts[0]}{marker},<br/>{parts[1].lstrip(', ')}"
            
            # Legacy/Alternate markers
            for alt in ["Pensioner Street", "पेंशनर स्ट्रीट", "பென்ஷனர் தெரு", "பென்ஷனர் வீதி", "Spencer Compound", "के पास", "அருகில்"]:
                if alt in addr:
                    parts = addr.split(alt, 1)
                    return f"{parts[0]}{alt},<br/>{parts[1].lstrip(', ')}"
                    
            # General fallback: split at the second comma if possible
            parts = [p.strip() for p in addr.split(",")]
            if len(parts) >= 3:
                first_half = ", ".join(parts[:2])
                second_half = ", ".join(parts[2:])
                return f"{first_half},<br/>{second_half}"
            elif len(parts) == 2:
                return f"{parts[0]},<br/>{parts[1]}"
            return addr

        data = {
            "bankNameEn": org["bank_name"]["en"],
            "bankNameHi": org["bank_name"]["hi"],
            "bankNameTa": org["bank_name"]["ta"],
            "officeNameEn": org["office_name"]["en"],
            "officeNameHi": org["office_name"]["hi"],
            "officeNameTa": org["office_name"]["ta"],
            "addressEnFormatted": format_address(ro_address_en, "Pensioner Street"),
            "addressHiFormatted": format_address(ro_address_hi, "पेंशनर स्ट्रीट"),
            "addressTaFormatted": format_address(ro_address_ta, "பென்ஷனர் வீதி"),
            "phone": contact["phone"],
            "email": contact["email"],
            "website": contact["website"],
            "headRoll": org.get("head_user_id")
        }

        # Load Logos
        logo_path = self.assets_dir / "doc_min.svg"
        if logo_path.exists():
            with logo_path.open("rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode('utf-8')
                data["bankLogo"] = f"data:image/svg+xml;base64,{logo_b64}"
                
        beti_path = self.assets_dir / "beti.svg"
        if beti_path.exists():
            with beti_path.open("rb") as f:
                beti_b64 = base64.b64encode(f.read()).decode('utf-8')
                data["betiLogo"] = f"data:image/svg+xml;base64,{beti_b64}"
                
        return data

    def render_doc(self, template_name: str, **kwargs) -> str:
        """Renders an HTML template with unified context."""
        template = self.env.get_template(template_name)
        
        # Calculate bank years
        bank_founding_date = datetime.date(1937, 2, 10)
        today = datetime.date.today()
        years = today.year - bank_founding_date.year
        if (today.month, today.day) < (bank_founding_date.month, bank_founding_date.day):
            years -= 1

        # Inject standard context
        context = {
            "org": self.org_data,
            "font_base_url": self.fonts_dir.as_uri() + "/",
            "datetime": datetime,
            "today": today,
            "bank_years": years
        }
        
        # Safely update with kwargs to avoid any internal clashes
        context.update(kwargs)
        
        return template.render(**context)

    def to_pdf(self, html: str) -> bytes:
        """Converts HTML to PDF using Headless Edge with optimized performance."""
        import datetime
        with tempfile.TemporaryDirectory() as tmp_dir:
            html_file = os.path.join(tmp_dir, "input.html")
            pdf_file = os.path.join(tmp_dir, "output.pdf")
            
            # Optimization: Instead of copying fonts for every PDF (slow), 
            # we use absolute file:/// URLs which Edge can read if --allow-file-access-from-files is set.
            # This significantly reduces I/O overhead during batch generation.
            
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html)
            
            infra = self.registry.get_infrastructure()
            edge_path = infra.get("browser_path", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
            
            # Performance & Stability Flags for Headless Edge
            cmd = [
                edge_path, 
                "--headless=new", 
                "--disable-gpu", 
                "--no-sandbox",
                "--disable-software-rasterizer",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--allow-file-access-from-files", # Crucial for absolute file:/// font URLs
                f"--print-to-pdf={pdf_file}", 
                "--no-pdf-header-footer", 
                html_file
            ]
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            try:
                # Increased timeout to 120s to handle high-density templates or slow disk I/O
                subprocess.run(cmd, check=True, timeout=120, startupinfo=startupinfo)
                
                # Robust verification of file writing
                # Some versions of Edge return success before the file is fully flushed to disk
                for _ in range(40):
                    if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 1024:
                        break
                    time.sleep(0.2)
                
                with open(pdf_file, "rb") as f:
                    return f.read()
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"PDF generation timed out (120s). Edge process may be hanging or blocked by security software.")
            except Exception as e:
                raise RuntimeError(f"PDF generation failed: {str(e)}")

    def resolve_staff(self, identifier: str) -> Dict[str, Any]:
        """Resolve roll number or name to trilingual signatory details. Optimized with caching."""
        identifier = str(identifier)
        from src.infrastructure.persistence.master_repository import MasterRepository
        from src.application.services.translation_service import DesignationMapper
        
        try:
            repo = MasterRepository()
            staff_records = repo.get_by_category("STAFF")
            found = next((s for s in staff_records if s.code == identifier or s.name_en == identifier or f"{s.name_en} ({s.metadata.get('designation')})" == identifier), None)
            
            if found:
                meta = found.metadata or {}
                # Prioritize metadata-based trilingual designations
                if meta.get("desig_hi") and meta.get("desig_ta"):
                    return {
                        "name": found.name_en, 
                        "name_hi": found.name_hi or found.name_en, 
                        "name_ta": found.name_local or found.name_en,
                        "roll": found.code, 
                        "desig_en": meta.get("desig_en", meta.get("designation", "Manager")),
                        "desig_hi": meta.get("desig_hi"), 
                        "desig_ta": meta.get("desig_ta")
                    }

                raw_desig = str(meta.get("designation", "")).upper()
                grade = str(meta.get("grade", "")).upper()
                
                # Precise IOB Grade-to-Designation Mapping
                if "VI" in grade: 
                    desig_key = "CHIEF REGIONAL MANAGER"
                elif "V" in grade and "IV" not in grade: 
                    desig_key = "SENIOR REGIONAL MANAGER"
                elif "IV" in grade: 
                    desig_key = "CHIEF MANAGER"
                else:
                    desig_key = None

                if desig_key:
                    trans = DesignationMapper.MAPPINGS[desig_key]
                    desig = {"en": desig_key.title(), "hi": trans["hi"], "ta": trans["ta"]}
                else:
                    desig = DesignationMapper.get_trilingual(raw_desig)

                return {
                    "name": found.name_en, "name_hi": found.name_hi or found.name_en, "name_ta": found.name_local or found.name_en,
                    "roll": found.code, "desig_en": desig["en"], "desig_hi": desig["hi"], "desig_ta": desig["ta"]
                }
        except Exception as exc:
            logger.warning("Failed to resolve staff %s: %s", identifier, exc)
        return {"name": identifier, "name_hi": identifier, "name_ta": identifier, "roll": "N/A", "desig_en": "Authorized Signatory", "desig_hi": "प्राधिकृत हस्ताक्षरकर्ता", "desig_ta": "அங்கீகரிக்கப்பட்ட கையொப்பமிட்டவர்"}
