from __future__ import annotations

import json
from html import escape

import streamlit as st
import streamlit.components.v1 as components

from src.core.config.config_loader import AppSettings


def inject_seo_metadata(settings: AppSettings) -> None:
    """Inject discoverability metadata into Streamlit's document head."""
    title = settings.app_title
    description = settings.app_description
    keywords = settings.app_keywords
    canonical = settings.public_url.strip()

    metadata = {
        "title": title,
        "description": description,
        "keywords": keywords,
        "canonical": canonical,
        "og:type": "website",
        "og:title": title,
        "og:description": description,
        "twitter:card": "summary",
        "twitter:title": title,
        "twitter:description": description,
    }
    if canonical:
        metadata["og:url"] = canonical

    json_ld = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": title,
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "description": description,
    }
    if canonical:
        json_ld["url"] = canonical

    script = f"""
    <script>
    const metadata = {json.dumps(metadata)};
    const jsonLd = {json.dumps(json_ld)};
    const doc = window.parent.document;

    function upsertMeta(selector, attrs) {{
      let element = doc.head.querySelector(selector);
      if (!element) {{
        element = doc.createElement("meta");
        doc.head.appendChild(element);
      }}
      Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
    }}

    doc.title = metadata.title;
    upsertMeta('meta[name="description"]', {{ name: "description", content: metadata.description }});
    upsertMeta('meta[name="keywords"]', {{ name: "keywords", content: metadata.keywords }});
    upsertMeta('meta[name="robots"]', {{ name: "robots", content: "index, follow" }});
    upsertMeta('meta[property="og:type"]', {{ property: "og:type", content: metadata["og:type"] }});
    upsertMeta('meta[property="og:title"]', {{ property: "og:title", content: metadata["og:title"] }});
    upsertMeta('meta[property="og:description"]', {{ property: "og:description", content: metadata["og:description"] }});
    upsertMeta('meta[name="twitter:card"]', {{ name: "twitter:card", content: metadata["twitter:card"] }});
    upsertMeta('meta[name="twitter:title"]', {{ name: "twitter:title", content: metadata["twitter:title"] }});
    upsertMeta('meta[name="twitter:description"]', {{ name: "twitter:description", content: metadata["twitter:description"] }});

    if (metadata.canonical) {{
      let canonical = doc.head.querySelector('link[rel="canonical"]');
      if (!canonical) {{
        canonical = doc.createElement("link");
        canonical.setAttribute("rel", "canonical");
        doc.head.appendChild(canonical);
      }}
      canonical.setAttribute("href", metadata.canonical);
      upsertMeta('meta[property="og:url"]', {{ property: "og:url", content: metadata["og:url"] }});
    }}

    let structuredData = doc.head.querySelector('script[type="application/ld+json"][data-ro-workstation]');
    if (!structuredData) {{
      structuredData = doc.createElement("script");
      structuredData.setAttribute("type", "application/ld+json");
      structuredData.setAttribute("data-ro-workstation", "true");
      doc.head.appendChild(structuredData);
    }}
    structuredData.textContent = JSON.stringify(jsonLd);
    </script>
    """
    components.html(script, height=0, width=0)

    st.markdown(
        f'<h1 style="position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;">{escape(title)}</h1>',
        unsafe_allow_html=True,
    )
