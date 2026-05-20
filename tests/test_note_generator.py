import unittest
from unittest.mock import patch

from src.application.services.notes.generator import NoteGenerator


class NoteGeneratorTests(unittest.TestCase):
    def test_generate_html_note_renders_reference_style_sections(self):
        extracted = {
            "ref_no": "RO/DGL/PLNG/2026-27/05/04",
            "date": "24.04.2026",
            "subject": "PAYMENT OF BILLS - BANNERS & OTHER PROMOTION MATERIALS - FEB 2026",
            "vendor_name": "Sri Gopi Digital Colour Xerox",
            "vendor_code": "VEN2409211",
            "intro_text": "Sri Gopi Digital Colour Xerox (VENDOR: VEN2409211) has presented bill for printing services availed from the vendor in Feb 2026. Details of the same are as follows:",
            "line_items": [
                {
                    "s_no": "1",
                    "date": "20.02.2026",
                    "details": "Banner printing",
                    "amount": 5000,
                    "rate": "100/pc",
                }
            ],
            "total": "5000",
            "summary_rows": [
                {"label": "Ro Budget", "value": "Rs 20,00,000/-"},
                {"label": "Utilised so far", "value": "Rs 38,696/-"},
            ],
            "recommendation_heading": "Department Observation & Recommendations",
            "recommendation_paragraphs": [
                "Since the aforementioned services were utilised for official purposes, we may make payment of Rs 5000/- to the vendor."
            ],
        }

        generator = NoteGenerator()
        with patch.object(generator.llm, "generate_json", return_value=extracted):
            html = generator.generate_html_note("Payment of Bills", "raw")

        self.assertIn("Regional Office, Dindigul", html)
        self.assertIn("Planning Department", html)
        self.assertIn("CM / SRM Sirs,", html)
        self.assertIn("Department Observation &amp; Recommendations", html)
        self.assertIn("Banner printing", html)
        self.assertIn("Ro Budget", html)

    def test_generate_html_note_uses_offline_fallback_structure(self):
        generator = NoteGenerator()
        with patch.object(generator.llm, "generate_json", return_value={"status": "offline_stub"}):
            html = generator.generate_html_note("Payment of Bills", "raw")

        self.assertIn("PAYMENT OF BILLS - DRAFT", html)
        self.assertIn("Manual Entry Required", html)
        self.assertIn("signature-table", html)


if __name__ == "__main__":
    unittest.main()
