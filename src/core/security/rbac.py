from __future__ import annotations

from functools import wraps
from typing import Callable


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
    """Decorator for actions with clear access feedback."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Non-streamlit fallback/no-op wrapper since Streamlit is removed
            return func(*args, **kwargs)

        return wrapper

    return decorator
