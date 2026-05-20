from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import logging
from pathlib import Path
from src.core.paths import project_path

logger = logging.getLogger(__name__)

class GraphicService:
    """Service to generate social media recognition posters (1080x1920)."""
    
    def __init__(self):
        self.width = 1080
        self.height = 1920
        self.fonts_dir = project_path("data", "fonts")
        self.assets_dir = project_path("src", "assets")
        
    def generate_milestone_poster(self, achievement: dict) -> bytes:
        """Creates a professional IOB-branded celebratory poster (1080x1920)."""
        # 1. Background (IOB Royal Blue Gradient)
        img = Image.new('RGB', (self.width, self.height), color='#0a1e45')
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Professional deep blue gradient
        for i in range(self.height):
            r = int(10 + (i / self.height) * 10)
            g = int(30 + (i / self.height) * 20)
            b = int(69 + (i / self.height) * 50)
            draw.line([(0, i), (self.width, i)], fill=(r, g, b))

        # 2. Institutional Branding
        self._draw_glow(img, (540, 960), 800, (212, 175, 55, 10)) # Subtle central glow

        # 3. Load Fonts
        font_huge = self._get_font("NotoSans-Bold.ttf", 130)
        font_large = self._get_font("NotoSans-Bold.ttf", 100)
        font_regular = self._get_font("NotoSans-Regular.ttf", 60)
        font_small = self._get_font("NotoSans-Bold.ttf", 65) # Highlighted Region
        font_label = self._get_font("NotoSans-Regular.ttf", 45)

        # 4. Celebration Mood (Favicon Rain with varying blur)
        try:
            favicon_path = os.path.join(self.assets_dir, "favicon.png")
            if os.path.exists(favicon_path):
                fav = Image.open(favicon_path).convert("RGBA")
                self._draw_favicon_rain(img, fav)
        except (OSError, ValueError) as exc:
            logger.warning("Could not draw favicon decoration: %s", exc)

        # 5. Official Branding Header
        try:
            logo_path = os.path.join(self.assets_dir, "2026logo_min.png")
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                logo_h = 140
                logo_w = int(logo.width * (logo_h / logo.height))
                logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                img.paste(logo, (self.width//2 - logo_w//2, 120), logo)
        except (OSError, ValueError) as exc:
            logger.warning("Could not draw logo on milestone poster: %s", exc)

        # Highlighted Region Name (Larger as requested)
        header_y = 320
        draw.text((self.width//2, header_y), "DINDIGUL REGION", fill="#d4af37", font=font_small, anchor="mm")
        
        # 6. Content Section
        draw.text((self.width//2, 600), "CONGRATULATIONS!", fill="#FFFFFF", font=font_large, anchor="mm")
        
        # Branch Name (Adaptive & Wrapped)
        branch_name = achievement.get("branch_name", "Unknown Branch").upper()
        import textwrap
        wrapped = textwrap.wrap(branch_name, width=18) # Slightly wider wrap
        
        curr_y = 850
        for line in wrapped:
            # Dynamically size each line to fit 950px width
            line_font = self._get_adaptive_font(line, 130, 950)
            
            # Drop shadow
            draw.text((self.width//2 + 5, curr_y + 5), line, fill=(0,0,0,200), font=line_font, anchor="mm")
            draw.text((self.width//2, curr_y), line, fill="#FFFFFF", font=line_font, anchor="mm")
            curr_y += 150

        # 7. Milestone Badge
        milestone = achievement.get("milestone", "50Cr+")
        param = achievement.get("parameter", "Business")
        
        badge_y = 1300
        badge_w, badge_h = 650, 240
        badge_box = [self.width//2 - badge_w//2, badge_y, self.width//2 + badge_w//2, badge_y + badge_h]
        
        draw.rounded_rectangle(badge_box, radius=30, fill="#d4af37")
        draw.text((self.width//2, badge_y + 90), milestone, fill="#0a1e45", font=font_huge, anchor="mm")
        draw.text((self.width//2, badge_y + 175), param.upper(), fill="#0a1e45", font=font_label, anchor="mm")

        # 8. Exact Breakthrough Date
        achievement_date = achievement.get("date")
        date_str = achievement_date.strftime("%d %B %Y").upper() if hasattr(achievement_date, "strftime") else str(achievement_date)

        footer_y = 1700
        draw.text((self.width//2, footer_y), "THRESHOLD CROSSED ON", fill="#cbd5e1", font=font_label, anchor="mm")
        draw.text((self.width//2, footer_y + 80), date_str, fill="#FFFFFF", font=font_regular, anchor="mm")

        # 9. Institutional Footer
        draw.line([(250, 1820), (830, 1820)], fill="#d4af37", width=3)
        draw.text((self.width//2, 1880), "INDIAN OVERSEAS BANK", fill="#d4af37", font=font_label, anchor="mm")

        # 10. Export
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format='PNG', optimize=True)
        return buf.getvalue()

    def _draw_favicon_rain(self, img, fav_img):
        """Draws a rain of favicons with varying scales and blurs."""
        import random
        for _ in range(80):
            # Random scale
            scale = random.uniform(0.3, 1.2)
            size = int(64 * scale)
            f = fav_img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Random blur (Depth of Field effect)
            blur_radius = random.uniform(0, 4)
            if blur_radius > 0.5:
                f = f.filter(ImageFilter.GaussianBlur(blur_radius))
            
            # Random position and rotation
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            angle = random.randint(0, 360)
            f = f.rotate(angle, expand=True)
            
            # Paste with varying transparency
            alpha = int(random.uniform(50, 150))
            f_mask = f.split()[3].point(lambda p: p * (alpha / 255.0))
            img.paste(f, (x, y), f_mask)

    def _get_adaptive_font(self, text: str, initial_size: int, max_width: int, is_bold: bool = True) -> ImageFont.FreeTypeFont:
        """Dynamically scales font size to fit within the specified width."""
        font_name = "NotoSans-Bold.ttf" if is_bold else "NotoSans-Regular.ttf"
        size = initial_size
        font = self._get_font(font_name, size)
        
        # Measure and reduce
        while size > 20:
            font = self._get_font(font_name, size)
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            if text_width <= max_width:
                break
            size -= 5
        return font

    def _get_font(self, name, size):
        font_path = os.path.join(self.fonts_dir, name)
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except OSError as exc:
            logger.debug("Could not load font %s: %s", font_path, exc)
        # Fallback to SegoeUI if NotoSans is missing or corrupted
        fallback_path = os.path.join(self.fonts_dir, "SegoeUI-Bold.ttf")
        if os.path.exists(fallback_path):
             return ImageFont.truetype(fallback_path, size)
        return ImageFont.load_default()

    def _draw_glow(self, img, pos, radius, color):
        """Draws a soft institutional radial glow."""
        glow = Image.new('RGBA', (radius*2, radius*2), (0,0,0,0))
        d = ImageDraw.Draw(glow)
        for i in range(radius):
            alpha = int(color[3] * (1 - i/radius))
            d.ellipse([radius-i, radius-i, radius+i, radius+i], outline=(color[0], color[1], color[2], alpha))
        img.paste(glow, (pos[0]-radius, pos[1]-radius), glow)

    def generate_performance_infographic(
        self,
        title: str,
        subtitle: str,
        metric_label: str,
        basis_label: str,
        date_str: str,
        top_branches: list[dict],
        bottom_branches: list[dict]
    ) -> bytes:
        """Generates a high-fidelity celebratory infographic poster (1080x1920) of top and bottom performers."""
        # 1. Base Gradient Canvas
        img = Image.new('RGB', (self.width, self.height), color='#070f2b')
        draw = ImageDraw.Draw(img, 'RGBA')
        
        for i in range(self.height):
            r = int(7 + (i / self.height) * 15)
            g = int(15 + (i / self.height) * 20)
            b = int(43 + (i / self.height) * 60)
            draw.line([(0, i), (self.width, i)], fill=(r, g, b))

        # 2. Glowing effects
        self._draw_glow(img, (200, 300), 500, (59, 130, 246, 25))  # Cyan/Blue glow top-left
        self._draw_glow(img, (880, 1600), 600, (139, 92, 246, 20)) # Purple/Violet glow bottom-right

        # 3. Official Logo Branding
        try:
            logo_path = os.path.join(self.assets_dir, "2026logo_min.png")
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                logo_h = 110
                logo_w = int(logo.width * (logo_h / logo.height))
                logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                img.paste(logo, (self.width//2 - logo_w//2, 70), logo)
        except Exception as exc:
            logger.warning("Could not render logo in infographic: %s", exc)

        # 4. Header Fonts & Typography
        font_title = self._get_font("NotoSans-Bold.ttf", 52)
        font_sub = self._get_font("NotoSans-Regular.ttf", 32)
        font_badge = self._get_font("NotoSans-Bold.ttf", 36)
        font_col_header = self._get_font("NotoSans-Bold.ttf", 32)
        font_rank = self._get_font("NotoSans-Bold.ttf", 26)
        font_val = self._get_font("NotoSans-Bold.ttf", 26)

        # Draw Institutional Titles
        draw.text((self.width//2, 200), "INDIAN OVERSEAS BANK", fill="#93c5fd", font=font_sub, anchor="mm")
        draw.text((self.width//2, 260), title.upper(), fill="#FFFFFF", font=font_title, anchor="mm")
        
        # Subtitle / Campaign Name
        draw.text((self.width//2, 320), subtitle.upper(), fill="#f59e0b", font=self._get_font("NotoSans-Bold.ttf", 28), anchor="mm")

        # Period Badge
        badge_text = f"  {date_str.upper()} PERFORMANCE LEAGUE  "
        bbox = font_badge.getbbox(badge_text)
        badge_w = bbox[2] - bbox[0] + 40
        badge_h = 64
        draw.rounded_rectangle(
            [self.width//2 - badge_w//2, 365, self.width//2 + badge_w//2, 365 + badge_h],
            radius=15,
            fill="#d4af37"
        )
        draw.text((self.width//2, 365 + badge_h//2), badge_text, fill="#070f2b", font=font_badge, anchor="mm")

        # Config / Info Bar
        info_str = f"METRIC: {metric_label.upper()}   |   BASIS: {basis_label.upper()}"
        draw.text((self.width//2, 465), info_str, fill="#93c5fd", font=self._get_font("NotoSans-Bold.ttf", 24), anchor="mm")

        # 5. Column Headers
        # Left (Top performers)
        draw.rounded_rectangle([50, 510, 510, 570], radius=10, fill=(16, 185, 129, 35), outline="#10b981", width=2)
        
        # Draw Gold Star Vector Icon
        import math
        cx_star, cy_star = 145, 540
        star_size = 18
        star_points = []
        for j in range(10):
            r = star_size if j % 2 == 0 else star_size / 2
            angle = j * 36 * (math.pi / 180) - math.pi / 2
            star_points.append((cx_star + r * math.cos(angle), cy_star + r * math.sin(angle)))
        draw.polygon(star_points, fill="#f59e0b")
        draw.text((180, 540), "TOP 10 BRANCHES", fill="#34d399", font=font_col_header, anchor="lm")
        
        # Right (Bottom performers)
        draw.rounded_rectangle([570, 510, 1030, 570], radius=10, fill=(239, 68, 68, 35), outline="#ef4444", width=2)
        
        # Draw Warning Triangle Vector Icon
        cx_tri, cy_tri = 635, 540
        tri_size = 18
        p1 = (cx_tri, cy_tri - tri_size)
        p2 = (cx_tri - tri_size * 1.1, cy_tri + tri_size * 0.8)
        p3 = (cx_tri + tri_size * 1.1, cy_tri + tri_size * 0.8)
        draw.polygon([p1, p2, p3], fill="#ef4444")
        # Draw exclamation mark inside warning triangle
        draw.line([(cx_tri, cy_tri - tri_size * 0.3), (cx_tri, cy_tri + tri_size * 0.2)], fill="#070f2b", width=3)
        draw.ellipse([cx_tri - 2, cy_tri + tri_size * 0.4, cx_tri + 2, cy_tri + tri_size * 0.5], fill="#070f2b")
        
        draw.text((670, 540), "BOTTOM 10 BRANCHES", fill="#f87171", font=font_col_header, anchor="lm")

        # 6. Draw Rows
        start_y = 600
        row_height = 105

        for i in range(10):
            y_pos = start_y + i * row_height

            # --- TOP PERFORMER ROW ---
            if i < len(top_branches):
                item = top_branches[i]
                bg_color = (255, 255, 255, 14) if i % 2 == 0 else (255, 255, 255, 6)
                draw.rounded_rectangle([50, y_pos, 510, y_pos + 95], radius=12, fill=bg_color)
                
                # Rank Badge
                rank_color = "#d4af37" if i < 3 else "#3b82f6"  # Gold for Top 3, Blue for rest
                draw.ellipse([65, y_pos + 22, 115, y_pos + 72], fill=rank_color)
                draw.text((90, y_pos + 47), str(i + 1), fill="#FFFFFF", font=font_rank, anchor="mm")
                
                # Branch Name (Adaptive)
                branch_font = self._get_adaptive_font(item["name"], 26, 220)
                draw.text((130, y_pos + 47), item["name"], fill="#FFFFFF", font=branch_font, anchor="lm")
                
                # Value
                draw.text((490, y_pos + 47), item["value"], fill="#34d399", font=font_val, anchor="rm")

            # --- BOTTOM PERFORMER ROW ---
            if i < len(bottom_branches):
                item = bottom_branches[i]
                bg_color = (255, 255, 255, 14) if i % 2 == 0 else (255, 255, 255, 6)
                draw.rounded_rectangle([570, y_pos, 1030, y_pos + 95], radius=12, fill=bg_color)
                
                # Rank Badge (Gray/Rose)
                draw.ellipse([585, y_pos + 22, 635, y_pos + 72], fill="#64748b")
                draw.text((610, y_pos + 47), str(item.get("rank", 10 - i)), fill="#FFFFFF", font=font_rank, anchor="mm")
                
                # Branch Name
                branch_font = self._get_adaptive_font(item["name"], 26, 220)
                draw.text((650, y_pos + 47), item["name"], fill="#FFFFFF", font=branch_font, anchor="lm")
                
                # Value
                draw.text((1010, y_pos + 47), item["value"], fill="#f87171", font=font_val, anchor="rm")

        # 7. Premium Footer Section
        footer_y = 1715
        draw.line([(150, footer_y), (930, footer_y)], fill="#d4af37", width=2)
        
        draw.text((self.width//2, footer_y + 45), "INDIAN OVERSEAS BANK  •  REGIONAL OFFICE DINDIGUL", fill="#94a3b8", font=self._get_font("NotoSans-Bold.ttf", 26), anchor="mm")
        draw.text((self.width//2, footer_y + 90), "Generated via Cockpit Executive Analytics Platform", fill="#64748b", font=self._get_font("NotoSans-Regular.ttf", 22), anchor="mm")

        # 8. Export as PNG bytes
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format='PNG', optimize=True)
        return buf.getvalue()
