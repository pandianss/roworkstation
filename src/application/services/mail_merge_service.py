from __future__ import annotations

import io
import pandas as pd
from typing import Any
from src.application.services.document import DocumentService
from jinja2 import Template


class MailMergeService:
    def __init__(self) -> None:
        self.doc_service = DocumentService()

    def process_merge(self, html_template: str, data_frame: pd.DataFrame) -> list[bytes]:
        """
        Merges a dataframe with an HTML template and returns a list of PDFs.
        """
        results = []
        template = Template(html_template)
        
        for _, row in data_frame.iterrows():
            # Convert row to dict for Jinja
            context = row.to_dict()
            rendered_html = template.render(**context)
            pdf_bytes = self.doc_service.generate_pdf_from_html(rendered_html)
            results.append(pdf_bytes)
            
        return results

    def process_merge_zip(self, template: str, df) -> bytes:
        """
        Run process_merge and return all generated PDFs as a single ZIP archive.
        File names inside the ZIP:
          - If the DataFrame has a 'NAME' column: 001_<NAME>.pdf
          - Otherwise: document_001.pdf
        Returns the ZIP as bytes suitable for st.download_button.
        """
        import io
        import zipfile
        import re

        pdfs: list[bytes] = self.process_merge(template, df)
        has_name_col = "NAME" in df.columns

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for idx, pdf_bytes in enumerate(pdfs, start=1):
                if has_name_col:
                    raw_name = str(df.iloc[idx - 1].get("NAME", f"document_{idx:03d}"))
                    safe_name = re.sub(r"[^\w\-]", "_", raw_name)[:40]
                    filename = f"{idx:03d}_{safe_name}.pdf"
                else:
                    filename = f"document_{idx:03d}.pdf"
                zf.writestr(filename, pdf_bytes)

        return zip_buffer.getvalue()
