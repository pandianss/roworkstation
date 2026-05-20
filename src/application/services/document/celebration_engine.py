import os
import json
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageChops
from src.core.paths import project_path

class CelebrationEngine:
    """
    Advanced Deterministic Image Generation Engine for Institutional Celebrations.
    Uses PIL for high-density, layered composition with adaptive typography.
    """
    
    CANVAS_WIDTH = 1080
    CANVAS_HEIGHT = 1920
    DPI = 300
    
    def __init__(self):
        self.themes_path = project_path("src", "assets", "themes")
        self.fonts_path = project_path("data", "fonts")
        self.themes = self._load_themes()
        
    def _load_themes(self) -> Dict[str, Any]:
        path = self.themes_path / "themes.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _get_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        path = self.fonts_path / font_name
        try:
            if not path.exists():
                raise FileNotFoundError
            return ImageFont.truetype(str(path), size)
        except (OSError, FileNotFoundError):
            # Fallback to SegoeUI which we verified is valid
            fallback_path = self.fonts_path / "SegoeUI-Regular.ttf"
            if fallback_path.exists():
                return ImageFont.truetype(str(fallback_path), size)
            return ImageFont.load_default()

    def _contains_tamil(self, text: str) -> bool:
        return any('\u0b80' <= char <= '\u0bff' for char in text)

    def _get_adaptive_font(self, text: str, initial_size: int, max_width: int, is_bold: bool = False) -> tuple:
        """Dynamically scales font size based on text length and width constraints."""
        size = initial_size
        
        # Decide font family based on language and availability
        if self._contains_tamil(text):
            font_file = "NotoSansTamil-Bold.ttf" if is_bold else "NotoSansTamil-Regular.ttf"
        else:
            # Use SegoeUI as primary default (GoogleSans in this repo is corrupted HTML)
            font_file = "SegoeUI-Bold.ttf" if is_bold else "SegoeUI-Regular.ttf"
            
        font = self._get_font(font_file, size)
        
        # Simple iterative scaling
        while size > 20:
            font = self._get_font(font_file, size)
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            if text_width <= max_width:
                break
            size -= 4
            
        return font, size

    def render_poster(self, data: Dict[str, Any], theme_key: str = "executive") -> Image.Image:
        """Renders a complete 1080x1920 poster based on theme and data."""
        theme = self.themes.get(theme_key, self.themes["executive"])
        theme_dir = self.themes_path / theme_key
        
        # 1. Create Base Canvas (Background with Aspect Fill)
        bg_path = theme_dir / theme["background"]
        if bg_path.exists():
            bg_img = Image.open(bg_path).convert("RGBA")
            # Calculate aspect fill
            bg_w, bg_h = bg_img.size
            aspect = bg_w / bg_h
            canvas_aspect = self.CANVAS_WIDTH / self.CANVAS_HEIGHT
            
            if aspect > canvas_aspect:
                # Bg is wider than canvas
                new_h = self.CANVAS_HEIGHT
                new_w = int(new_h * aspect)
            else:
                # Bg is taller than canvas
                new_w = self.CANVAS_WIDTH
                new_h = int(new_w / aspect)
                
            bg_img = bg_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            # Crop to center
            left = (new_w - self.CANVAS_WIDTH) // 2
            top = (new_h - self.CANVAS_HEIGHT) // 2
            canvas = bg_img.crop((left, top, left + self.CANVAS_WIDTH, top + self.CANVAS_HEIGHT))
        else:
            canvas = Image.new("RGBA", (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), "#020617")
            
        draw = ImageDraw.Draw(canvas)
        
        # 2. Branding Layer (Top Logo)
        logo_path = project_path("src", "assets", "2026logo_min.png")
        if logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")
            logo_w = 400
            logo_h = int(logo.height * (logo_w / logo.width))
            logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
            canvas.paste(logo, ((self.CANVAS_WIDTH - logo_w) // 2, 80), logo)
            
        # 3. Typography Layer (Drawn FIRST)
        header_text = data.get("milestone_type", "BIRTHDAY")
        header_font, _ = self._get_adaptive_font("WARMEST WISHES ON YOUR", 32, 800)
        draw.text((self.CANVAS_WIDTH // 2, 340), "WARMEST WISHES ON YOUR", font=header_font, fill=theme["primary_color"], anchor="mm")
        
        title_font, _ = self._get_adaptive_font(header_text, 140, 900, is_bold=True)
        draw.text((self.CANVAS_WIDTH // 2, 420), header_text, font=title_font, fill=theme["secondary_color"], anchor="mm")

        # 4. Decoration Layer (Center Piece - User Provided PNG)
        dec_path = theme_dir / theme["decoration"]
        if dec_path.exists():
            dec = Image.open(dec_path).convert("RGBA")
            target_w = 700
            dec_w = target_w
            dec_h = int(dec.height * (dec_w / dec.width))
            dec = dec.resize((dec_w, dec_h), Image.Resampling.LANCZOS)
            
            # Position at center - perfectly framed between title and name
            dec_pos = ((self.CANVAS_WIDTH - dec_w) // 2, 580)
            
            # Paste as a normal sticker with its alpha mask
            canvas.paste(dec, dec_pos, dec)

        # 5. Staff Info Layer (Increased spacing to prevent overlap)
        
        # Staff Name
        name_en = data.get("name_en", "STAFF NAME")
        name_font, name_size = self._get_adaptive_font(name_en, 120, 950, is_bold=True)
        draw.text((self.CANVAS_WIDTH // 2, 1300), name_en, font=name_font, fill=theme["secondary_color"], anchor="mm")
        
        # Designation - Pushed down to avoid overlap with name
        desig = data.get("designation", "")
        desig_font, _ = self._get_adaptive_font(desig, 42, 850)
        draw.text((self.CANVAS_WIDTH // 2, 1420), desig, font=desig_font, fill=theme["primary_color"], anchor="mm")
        
        # Branch Info Card - Improved visibility and shape
        branch_name = data.get("branch_name", "BRANCH NAME")
        box_w, box_h = 920, 240
        box_x = (self.CANVAS_WIDTH - box_w) // 2
        box_y = 1530
        
        # Premium Rounded Card with Navy/Gold theme
        # Use a darker, more opaque background for better contrast
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=40,
            fill=(2, 6, 23, 180), # Deep navy, more opaque
            outline=theme["primary_color"],
            width=3
        )
        
        branch_label_font, _ = self._get_adaptive_font("BRANCH", 28, 700)
        draw.text((self.CANVAS_WIDTH // 2, box_y + 60), "BRANCH", font=branch_label_font, fill=theme["primary_color"], anchor="mm")
        
        branch_font, _ = self._get_adaptive_font(branch_name, 80, 850, is_bold=True)
        draw.text((self.CANVAS_WIDTH // 2, box_y + 145), branch_name, font=branch_font, fill="#FFFFFF", anchor="mm")

        # Footer
        footer_text = "With warm wishes from Indian Overseas Bank – Dindigul Region"
        footer_font, _ = self._get_adaptive_font(footer_text, 28, 950)
        draw.text((self.CANVAS_WIDTH // 2, 1840), footer_text, font=footer_font, fill=(255, 255, 255, 80), anchor="mm")

        return canvas

    def render_anniversary(self, data: Dict[str, Any], theme_key: str = "executive") -> Image.Image:
        """Renders a complete 1080x1920 branch anniversary poster."""
        theme = self.themes.get(theme_key, self.themes["executive"])
        theme_dir = self.themes_path / theme_key
        
        # 1. Create Base Canvas (Background with Aspect Fill)
        bg_path = theme_dir / theme["background"]
        if bg_path.exists():
            bg_img = Image.open(bg_path).convert("RGBA")
            bg_w, bg_h = bg_img.size
            aspect = bg_w / bg_h
            canvas_aspect = self.CANVAS_WIDTH / self.CANVAS_HEIGHT
            
            if aspect > canvas_aspect:
                new_h = self.CANVAS_HEIGHT
                new_w = int(new_h * aspect)
            else:
                new_w = self.CANVAS_WIDTH
                new_h = int(new_w / aspect)
                
            bg_img = bg_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left = (new_w - self.CANVAS_WIDTH) // 2
            top = (new_h - self.CANVAS_HEIGHT) // 2
            canvas = bg_img.crop((left, top, left + self.CANVAS_WIDTH, top + self.CANVAS_HEIGHT))
        else:
            canvas = Image.new("RGBA", (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), "#020617")
            
        draw = ImageDraw.Draw(canvas)
        
        # 2. Branding Layer
        logo_path = project_path("src", "assets", "2026logo_min.png")
        if logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")
            logo_w = 400
            logo_h = int(logo.height * (logo_w / logo.width))
            logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
            canvas.paste(logo, ((self.CANVAS_WIDTH - logo_w) // 2, 80), logo)
            
        # 3. Typography Layer (Top)
        draw.text((self.CANVAS_WIDTH // 2, 340), "HEARTY CONGRATULATIONS", font=self._get_font("SegoeUI-Bold.ttf", 32), fill=theme["primary_color"], anchor="mm")
        draw.text((self.CANVAS_WIDTH // 2, 420), "ANNIVERSARY", font=self._get_font("SegoeUI-Bold.ttf", 120), fill=theme["secondary_color"], anchor="mm")

        # 4. Milestone Badge Layer (Using the new clean dynamic badge)
        badge_path = theme_dir / "anniversary_badge.png"
        if not badge_path.exists():
            # Fallback
            badge_path = theme_dir / theme["decoration"]
            
        if badge_path.exists():
            badge = Image.open(badge_path).convert("RGBA")
            target_w = 750
            badge_w = target_w
            badge_h = int(badge.height * (badge_w / badge.width))
            badge = badge.resize((badge_w, badge_h), Image.Resampling.LANCZOS)
            
            badge_pos = ((self.CANVAS_WIDTH - badge_w) // 2, 510)
            canvas.paste(badge, badge_pos, badge)
            
            # Draw years inside the badge with improved spacing
            years = str(data.get("years", "0"))
            # Smaller, more elegant font size for the number
            years_font = self._get_font("SegoeUI-Bold.ttf", 200) 
            
            # Draw "YEARS OF EXCELLENCE" or similar below the number
            # Center the number in the blue circle of the new badge
            draw.text((self.CANVAS_WIDTH // 2, 510 + (badge_h // 2) - 10), years, font=years_font, fill="#FFFFFF", anchor="mm")
            draw.text((self.CANVAS_WIDTH // 2, 510 + (badge_h // 2) + 100), "YEARS", font=self._get_font("SegoeUI-Bold.ttf", 44), fill=theme["primary_color"], anchor="mm")

        # 5. Branch Details
        branch_name = data.get("branch_name", "BRANCH NAME")
        name_font, _ = self._get_adaptive_font(branch_name, 110, 950, is_bold=True)
        draw.text((self.CANVAS_WIDTH // 2, 1300), branch_name, font=name_font, fill=theme["secondary_color"], anchor="mm")
        
        region_name = data.get("region_name", "Regional Office")
        region_font = self._get_font("SegoeUI-Regular.ttf", 40)
        draw.text((self.CANVAS_WIDTH // 2, 1400), region_name, font=region_font, fill=theme["primary_color"], anchor="mm")
        
        # Open Date Card
        open_date = data.get("open_date", "")
        box_w, box_h = 920, 180
        box_x = (self.CANVAS_WIDTH - box_w) // 2
        box_y = 1530
        
        draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=40, fill=(2, 6, 23, 180), outline=theme["primary_color"], width=3)
        draw.text((self.CANVAS_WIDTH // 2, box_y + 90), f"Opened on {open_date}", font=self._get_font("SegoeUI-Bold.ttf", 52), fill="#FFFFFF", anchor="mm")

        # Footer
        footer_text = "Celebrating the journey of excellence since 1937"
        draw.text((self.CANVAS_WIDTH // 2, 1840), footer_text, font=self._get_font("SegoeUI-Regular.ttf", 28), fill=(255, 255, 255, 100), anchor="mm")

        return canvas
