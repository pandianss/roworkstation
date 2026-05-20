import os
import base64
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from src.core.paths import project_path
from playwright.sync_api import sync_playwright

class VisitingCardEngine:
    """
    High-Resolution Trilingual Visiting Card Generation Engine.
    Uses Playwright (Headless Browser) for perfect trilingual typography.
    """
    
    def __init__(self):
        self.templates_path = project_path("src", "infrastructure", "templates")
        self.assets_path = project_path("src", "assets")
        self.env = Environment(loader=FileSystemLoader(str(self.templates_path)), cache_size=0)

    def _get_base64_data(self, path: os.PathLike, mime: str = "image/png") -> str:
        if not os.path.exists(path):
            return ""
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            return f"data:{mime};base64,{encoded}"

    def render_card(self, data: Dict[str, Any]) -> list[bytes]:
        """Renders high-resolution front and back visiting card PNGs."""
        
        # Prepare Template Data
        template = self.env.get_template("visiting_card.html")
        
        # Load trilingual bank names dynamically from parameters.yaml
        from src.core.registry.parameter_service import ParameterRegistry
        try:
            registry = ParameterRegistry()
            org = registry.get_org_info()
            bank_name = org.get("bank_name", {})
            data.setdefault("bank_name_en", bank_name.get("en", "Indian Overseas Bank"))
            data.setdefault("bank_name_hi", bank_name.get("hi", "इण्डियन ओवरसीज़ बैंक"))
            data.setdefault("bank_name_ta", bank_name.get("ta", "இண்டியன் ஓவர்சீஸ் பேங்க்"))
        except Exception:
            data.setdefault("bank_name_en", "Indian Overseas Bank")
            data.setdefault("bank_name_hi", "इण्डियन ओवरसीज़ बैंक")
            data.setdefault("bank_name_ta", "இண்டியன் ஓவர்சீஸ் பேங்க்")
        
        assets = {
            "logo_url": self._get_base64_data(self.assets_path / "favicon.svg", mime="image/svg+xml"),
            "logo_back_url": self._get_base64_data(self.assets_path / "2026logo_min.svg", mime="image/svg+xml"),
            "phone_icon": self._get_base64_data(self.assets_path / "themes/executive/vc_phone.png"),
            "mobile_icon": self._get_base64_data(self.assets_path / "themes/executive/vc_mobile.png"),
            "email_icon": self._get_base64_data(self.assets_path / "themes/executive/vc_email.png"),
            "web_icon": self._get_base64_data(self.assets_path / "themes/executive/vc_web.png"),
            "font_en": base64.b64encode(open(project_path("data", "fonts", "SegoeUI-Regular.ttf"), "rb").read()).decode(),
            "font_hi": base64.b64encode(open(project_path("data", "fonts", "NotoSansDevanagari-Regular.ttf"), "rb").read()).decode(),
            "font_ta": base64.b64encode(open(project_path("data", "fonts", "NotoSansTamil-Regular.ttf"), "rb").read()).decode(),
            "facebook_icon": self._get_base64_data(self.assets_path / "facebook_icon.svg", mime="image/svg+xml"),
            "twitter_icon": self._get_base64_data(self.assets_path / "twitter_icon.svg", mime="image/svg+xml"),
            "instagram_icon": self._get_base64_data(self.assets_path / "instagram_icon.svg", mime="image/svg+xml"),
            "linkedin_icon": self._get_base64_data(self.assets_path / "linkedin_icon.svg", mime="image/svg+xml")
        }
        
        html_content = template.render(**data, **assets)
        
        # Windows ProactorEventLoop fix for Playwright subprocess
        import asyncio
        import sys
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        pages_bytes = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1050, "height": 630}, device_scale_factor=2)
            page.set_content(html_content)
            page.wait_for_timeout(200) # Slightly more for Tamil font
            
            # Capture Front
            pages_bytes.append(page.locator("#front").screenshot(type="png"))
            # Capture Back
            pages_bytes.append(page.locator("#back").screenshot(type="png"))
            
            browser.close()
            
        return pages_bytes
