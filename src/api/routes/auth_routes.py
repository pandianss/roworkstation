from __future__ import annotations

import getpass

from fastapi import APIRouter

from src.application.services.admin_service import AdminService

router = APIRouter()


@router.get("/me")
def get_current_user():
    """
    Resolve the current workstation user from the OS username,
    look them up in master data, and return their portal assignment.

    portal values:
      "ro"     → ADMIN role → Regional Office Portal
      "branch" → USER role with assigned branches → Branch Portal
      "guest"  → unrecognised / GUEST → Guest Portal
    """
    username = getpass.getuser()
    admin_svc = AdminService()
    user = admin_svc.get_user(username)

    if not user:
        return {
            "username": username,
            "name": username,
            "role": "GUEST",
            "portal": "guest",
            "assigned_branches": [],
            "dept": "ALL",
        }

    # Determine which portal to send the user to
    if user.role == "ADMIN":
        portal = "ro"
    elif user.role == "USER" and user.assigned_branches:
        portal = "branch"
    else:
        portal = "guest"

    return {
        "username": user.username,
        "name": user.name or user.username,
        "role": user.role,
        "portal": portal,
        "assigned_branches": user.assigned_branches or [],
        "dept": user.dept or "ALL",
    }
