from __future__ import annotations

from functools import wraps
from typing import Callable

import streamlit as st


ROLE_HIERARCHY = {
    "USER": 1,
    "MANAGER": 2,
    "GUARDIAN": 2,
    "ADMIN": 3,
}

PERMISSIONS = {
    "view_dashboard": {"USER", "MANAGER", "GUARDIAN", "ADMIN"},
    "manage_users": {"ADMIN"},
    "manage_guardian": {"GUARDIAN", "ADMIN"},
    "run_operations": {"MANAGER", "ADMIN"},
    "view_mis": {"USER", "MANAGER", "GUARDIAN", "ADMIN"},
}


def has_permission(role: str | None, permission: str) -> bool:
    allowed = PERMISSIONS.get(permission, set())
    return bool(role and role in allowed)


def require_permission(permission: str) -> Callable:
    """Decorator for Streamlit actions with clear access feedback."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            role = st.session_state.get("role")
            if not has_permission(role, permission):
                st.error("You do not have permission to perform this action.")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator
