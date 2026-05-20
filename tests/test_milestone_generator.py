import unittest
from unittest.mock import MagicMock

from PIL import Image

from src.application.services.document.milestones import MilestoneGenerator


class MilestoneGeneratorTests(unittest.TestCase):
    def test_legacy_staff_milestone_method_returns_png_bytes(self):
        engine = MagicMock()
        generator = MilestoneGenerator(engine)
        generator.image_engine = MagicMock()
        generator.image_engine.render_poster.return_value = Image.new("RGBA", (16, 16), "#ffffff")

        result = generator.generate_staff_milestone(
            {"roll": "123", "name": "Staff Member", "desig_en": "Manager"},
            "BIRTHDAY",
            "Regional Office",
        )

        self.assertTrue(result.startswith(b"\x89PNG"))
        generator.image_engine.render_poster.assert_called_once()
        engine.render_doc.assert_not_called()
        engine.to_pdf.assert_not_called()

    def test_legacy_anniversary_note_method_returns_pdf_bytes(self):
        engine = MagicMock()
        engine.render_doc.return_value = "<html>note</html>"
        engine.to_pdf.return_value = b"%PDF"
        generator = MilestoneGenerator(engine)

        result = generator.generate_anniversary_note({"branch_name": "Main"})

        self.assertEqual(result, b"%PDF")
        engine.to_pdf.assert_called_once_with("<html>note</html>")

    def test_staff_milestone_uses_pil_image_engine_without_html_photo_fields(self):
        engine = MagicMock()
        generator = MilestoneGenerator(engine)
        generator.image_engine = MagicMock()
        generator.image_engine.render_poster.return_value = Image.new("RGBA", (16, 16), "#ffffff")

        generator.generate_staff_milestone_image(
            {"roll": "NO_PHOTO", "name": "Divya C B", "name_ta": "Divya C B", "desig_en": "Manager"},
            "BIRTHDAY",
            "Ayyakudi",
        )

        args, kwargs = generator.image_engine.render_poster.call_args
        self.assertEqual(args[0]["name_en"], "Divya C B")
        self.assertEqual(args[0]["designation"], "Manager")
        self.assertEqual(args[0]["branch_name"], "Ayyakudi")
        self.assertNotIn("has_photo", args[0])
        self.assertNotIn("photo_url", args[0])
        self.assertEqual(kwargs["theme_key"], "executive")


if __name__ == "__main__":
    unittest.main()
