from __future__ import annotations

import getpass

from src.application.services.admin_service import AdminService
from src.application.services.session_service import SessionService
from src.core.config.config_loader import get_app_settings
from src.domain.schemas import UserAccess


def resolve_current_user() -> UserAccess:
    """Resolve the current workstation user with admin override support."""
    import getpass
    
    username = getpass.getuser()
        
    session_service = SessionService()
    admin_service = AdminService()
    settings = get_app_settings()

    # Base user object from Master Data or fallback to Guest
    user = admin_service.get_user(username)
    if not user:
        user = UserAccess(
            username=username,
            role="GUEST",
            dept="ALL",
            depts=["ALL"],
            name=username,
        )

    # Check for active session override (Elevated Access)
    if session_service.is_session_active(username, settings.session_timeout_hours):
        user.role = "ADMIN"
        # Optional: Add departments if not present
        if "ALL" not in user.depts:
            user.depts.append("ALL")

    return user
