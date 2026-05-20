from __future__ import annotations

from html import escape


class _OfflineLLM:
    def generate_json(self, title: str, raw_text: str | None = None) -> dict:
        return {"status": "offline_stub"}


class NoteGenerator:
    def __init__(self, llm: object | None = None) -> None:
        self.llm = llm or _OfflineLLM()

    def generate_html_note(self, title: str, raw_text: str) -> str:
        data = self.llm.generate_json(title, raw_text) or {}
        if data.get("status") == "offline_stub":
            data = self._fallback(title)
        return self._render(data)

    @staticmethod
    def _fallback(title: str) -> dict:
        subject = f"{title or 'Office Note'} - Draft".upper()
        return {
            "ref_no": "RO/DGL/NOTE/DRAFT",
            "date": "",
            "subject": subject,
            "intro_text": "Manual Entry Required",
            "line_items": [],
            "total": "",
            "summary_rows": [],
            "recommendation_heading": "Department Observation & Recommendations",
            "recommendation_paragraphs": ["Manual Entry Required"],
        }

    def _render(self, data: dict) -> str:
        line_rows = "".join(
            "<tr>"
            f"<td>{escape(str(item.get('s_no', '')))}</td>"
            f"<td>{escape(str(item.get('date', '')))}</td>"
            f"<td>{escape(str(item.get('details', '')))}</td>"
            f"<td>{escape(str(item.get('rate', '')))}</td>"
            f"<td>{escape(str(item.get('amount', '')))}</td>"
            "</tr>"
            for item in data.get("line_items", [])
        )
        if not line_rows:
            line_rows = '<tr><td colspan="5">Manual Entry Required</td></tr>'

        summary_rows = "".join(
            f"<tr><th>{escape(str(row.get('label', '')))}</th><td>{escape(str(row.get('value', '')))}</td></tr>"
            for row in data.get("summary_rows", [])
        )

        recommendations = "".join(
            f"<p>{escape(str(paragraph))}</p>" for paragraph in data.get("recommendation_paragraphs", [])
        )

        return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: Arial, sans-serif; color: #111827; line-height: 1.45; }}
    .note {{ max-width: 860px; margin: 0 auto; padding: 32px; }}
    .center {{ text-align: center; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    th, td {{ border: 1px solid #9ca3af; padding: 8px; text-align: left; }}
    .signature-table td {{ height: 72px; vertical-align: bottom; text-align: center; }}
  </style>
</head>
<body>
  <main class="note">
    <h2 class="center">Regional Office, Dindigul</h2>
    <h3 class="center">Planning Department</h3>
    <p><strong>Ref:</strong> {escape(str(data.get("ref_no", "")))}<br>
    <strong>Date:</strong> {escape(str(data.get("date", "")))}</p>
    <h3>{escape(str(data.get("subject", "")))}</h3>
    <p>CM / SRM Sirs,</p>
    <p>{escape(str(data.get("intro_text", "")))}</p>
    <table>
      <thead><tr><th>S.No</th><th>Date</th><th>Details</th><th>Rate</th><th>Amount</th></tr></thead>
      <tbody>{line_rows}</tbody>
    </table>
    <p><strong>Total:</strong> {escape(str(data.get("total", "")))}</p>
    <table>{summary_rows}</table>
    <h3>{escape(str(data.get("recommendation_heading", "Department Observation & Recommendations")))}</h3>
    {recommendations}
    <table class="signature-table">
      <tr><td>Officer</td><td>Manager</td><td>CM / SRM</td></tr>
    </table>
  </main>
</body>
</html>
"""
