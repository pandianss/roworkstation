from __future__ import annotations
import streamlit as st
from src.application.services.document import DocumentService
from src.application.services.task_service import TaskService
from src.application.services.circular_service import CircularService
from src.application.services.returns_service import ReturnsService
from src.application.services.guardian_service import GuardianService
from src.application.services.mail_merge_service import MailMergeService
from src.application.use_cases.mis.service import MISAnalyticsService
from src.application.use_cases.global_search import GlobalSearchService
from src.application.services.master_service import MasterService

@st.cache_resource
def get_doc_service_v4():
    return DocumentService()

@st.cache_resource
def get_task_service():
    return TaskService()

@st.cache_resource
def get_circular_service():
    return CircularService()

@st.cache_resource
def get_returns_service():
    return ReturnsService()

@st.cache_resource
def get_guardian_service():
    return GuardianService()

@st.cache_resource
def get_mm_service():
    return MailMergeService()

@st.cache_resource
def get_mis_service():
    return MISAnalyticsService()

@st.cache_resource
def get_search_service():
    return GlobalSearchService()

@st.cache_resource
def get_master_service():
    return MasterService()

@st.cache_resource
def get_achievement_service():
    from src.application.services.achievement_service import AchievementService
    return AchievementService()
