from __future__ import annotations

from importlib import import_module


PAGE_REGISTRY = {
    "Dashboard": "src.interface.streamlit.pages.dashboard",
    "Operations": "src.interface.streamlit.pages.operational_wizards",
    "Operations & Returns": "src.interface.streamlit.pages.operational_wizards",
    "Document Hub": "src.interface.streamlit.pages.operational_wizards",
    "Document Center": "src.interface.streamlit.pages.operational_wizards",
    "MIS": "src.interface.streamlit.pages.mis",
    "Business Analytics": "src.interface.streamlit.pages.mis",
    "Office Note Generator": "src.interface.streamlit.pages.operational_wizards",
    "Returns & Compliance": "src.interface.streamlit.pages.returns",
    "Coordination Center": "src.interface.streamlit.pages.coordination",
    "Campaign Management": "src.interface.streamlit.pages.campaigns",
    "DICGC Return": "src.interface.streamlit.pages.dicgc",
    "Policy & Product Archive": "src.interface.streamlit.pages.knowledge",
    "Field Guardian": "src.interface.streamlit.pages.guardian",
    "Branch Visits": "src.interface.streamlit.pages.visits",
    "Admin": "src.interface.streamlit.pages.admin",
    "Letter Generator": "src.interface.streamlit.pages.letter_generator",
    "Branch Portal": "src.interface.streamlit.pages.branch_portal",
    "Guest Portal": "src.interface.streamlit.pages.guest_portal",
    "Anniversary Portal": "src.interface.streamlit.pages.anniversary_portal",
    "High Value DD Note": "src.interface.streamlit.pages.high_value_dd",
    "Office Note Hub": "src.interface.streamlit.pages.office_note_hub",
    "Visiting Card Wizard": "src.interface.streamlit.pages.visiting_card_wizard",
    "Central Archive": "src.interface.streamlit.pages.archive",
    "Account Performance": "src.interface.streamlit.pages.account_performance",
}


def render_page(page_name: str) -> None:
    module = import_module(PAGE_REGISTRY[page_name])
    module.render()

# Trigger hot-reload cache clear on change 8
