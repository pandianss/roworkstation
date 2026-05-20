import unittest
from unittest.mock import patch

import streamlit as st

from src.interface.streamlit.pages.anniversary_portal import _get_html_preview, _month_sort_key


class AnniversaryPortalTests(unittest.TestCase):
    def test_month_sorting_ignores_missing_values_before_strptime(self):
        raw_months = ["January", float("nan"), "March", None, "February"]
        cleaned = [str(month) for month in raw_months if isinstance(month, str)]
        self.assertEqual(sorted(cleaned, key=_month_sort_key), ["January", "February", "March"])

    def test_html_preview_decodes_utf8_bytes(self):
        st.session_state["preview_ok"] = b"<html>ok</html>"
        self.assertEqual(_get_html_preview("preview_ok"), "<html>ok</html>")

    def test_html_preview_clears_binary_pdf_bytes(self):
        st.session_state["preview_pdf"] = b"%PDF-\xd3"
        with patch("src.interface.streamlit.pages.anniversary_portal.st.warning") as warning:
            self.assertIsNone(_get_html_preview("preview_pdf"))
        self.assertNotIn("preview_pdf", st.session_state)
        warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
