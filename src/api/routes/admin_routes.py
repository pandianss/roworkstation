"""
Admin API Routes
================
All endpoints are protected by the X-Admin-Password header.
These are internal-only operations for data ingestion and master management.
"""
from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, File, UploadFile
from pydantic import BaseModel

from src.core.config.config_loader import get_app_settings

router = APIRouter()


# ── Auth dependency ──────────────────────────────────────────────────────────

def _require_admin(x_admin_password: str = Header(default="")) -> None:
    """Validates the X-Admin-Password header against the configured admin password."""
    settings = get_app_settings()
    if x_admin_password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password.")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_val(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _safe_rows(records: list[dict]) -> list[dict]:
    return [{k: _safe_val(v) for k, v in row.items()} for row in records]


# ────────────────────────────────────────────────────────────────────────────
# USERS & ACCESS
# ────────────────────────────────────────────────────────────────────────────

@router.get("/users", dependencies=[Depends(_require_admin)])
def list_users():
    """
    Return all users derived from staff master + explicit admin overrides.
    Each user includes: username, name, role, portal, dept, assigned_branches,
    designation, grade.
    """
    try:
        from src.application.services.admin_service import AdminService
        svc = AdminService()
        users = svc.list_users()
        return {
            "users": [u.model_dump() for u in users],
            "total": len(users),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class UserRoleUpdate(BaseModel):
    role: str                           # ADMIN | USER | GUEST
    dept: Optional[str] = "ALL"
    assigned_branches: Optional[list[str]] = []


@router.put("/users/{username}", dependencies=[Depends(_require_admin)])
def update_user_role(username: str, payload: UserRoleUpdate):
    """Update a user's role, department and branch assignments."""
    try:
        from src.application.services.admin_service import AdminService
        svc = AdminService()
        ok = svc.update_user(
            username,
            role=payload.role,
            dept=payload.dept or "ALL",
            depts=[payload.dept or "ALL"],
            assigned_branches=payload.assigned_branches or [],
        )
        if not ok:
            # User not in explicit list — add them
            svc.add_user(username, role=payload.role, dept=payload.dept or "ALL")
            svc.assign_branches_to_user(username, payload.assigned_branches or [])
        return {"status": "ok", "username": username}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ────────────────────────────────────────────────────────────────────────────
# MIS INGESTION
# ────────────────────────────────────────────────────────────────────────────

@router.get("/mis/files", dependencies=[Depends(_require_admin)])
def list_mis_files():
    """
    Return a list of all Excel files that have been ingested into the MIS store,
    along with their ingestion timestamps.
    """
    try:
        from src.infrastructure.persistence.mis_repository import MISRepository
        from sqlalchemy import text

        repo = MISRepository()
        session = repo.session_factory()
        rows = session.execute(
            text("SELECT filename, ingested_at FROM ingested_files ORDER BY ingested_at DESC")
        ).fetchall()
        session.close()

        files = [{"filename": r[0], "ingested_at": str(r[1])} for r in rows]
        available_dates = [str(d) for d in repo.get_available_dates()]

        return {
            "files": files,
            "total_files": len(files),
            "available_dates": available_dates,
            "total_dates": len(available_dates),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/mis/ingest", dependencies=[Depends(_require_admin)])
def trigger_mis_ingest(force: bool = Query(False, description="Force re-ingest all files even if already logged")):
    """
    Trigger MIS Excel ingestion from the configured files directory.
    Returns how many records were loaded and which dates are now available.
    """
    try:
        from src.application.use_cases.mis.service import MISAnalyticsService
        svc = MISAnalyticsService()
        df = svc.get_data(force_ingest=True)
        available_dates = svc.get_available_dates()
        return {
            "status": "ok",
            "records_loaded": len(df),
            "available_dates": [str(d) for d in available_dates],
            "message": f"Ingestion complete. {len(df)} records across {len(available_dates)} dates.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/mis/upload", dependencies=[Depends(_require_admin)])
def upload_mis_file(file: UploadFile = File(...)):
    """
    Upload an MIS Excel file, save it to the mis input directory,
    and trigger the ingestion process.
    """
    try:
        from src.application.use_cases.mis.service import MISAnalyticsService
        svc = MISAnalyticsService()
        
        # Ensure directories exist
        svc.mis_dir.mkdir(parents=True, exist_ok=True)
        svc.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # We must verify it's an xlsx file
        if not file.filename.endswith(".xlsx"):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a valid .xlsx Excel file.")
        
        # Clean up any pre-existing archive file of the same name to prevent shutil.move issues
        archive_path = svc.archive_dir / file.filename
        if archive_path.exists():
            archive_path.unlink()
            
        # Clean up any pre-existing input file of the same name
        input_path = svc.mis_dir / file.filename
        if input_path.exists():
            input_path.unlink()
            
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            while content := file.file.read(1024 * 1024):
                buffer.write(content)
                
        # Trigger ingestion
        summaries = svc.sync_database()
        available_dates = svc.get_available_dates()
        
        # Calculate how many records were loaded total in this ingestion run
        total_records = sum(s.get("count", 0) for s in summaries)
        
        return {
            "status": "ok",
            "message": f"Successfully uploaded and ingested '{file.filename}'.",
            "filename": file.filename,
            "summaries": summaries,
            "records_loaded": total_records,
            "available_dates": [str(d) for d in available_dates],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/mis/files/{filename}", dependencies=[Depends(_require_admin)])
def delete_mis_file(filename: str):
    """
    Remove a file's ingest log entry so it can be re-ingested.
    Does NOT delete the MIS records themselves — use /mis/purge-date for that.
    """
    try:
        from src.infrastructure.persistence.mis_repository import MISRepository
        repo = MISRepository()
        removed = repo.delete_ingested_file(filename)
        if not removed:
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found in ingest log.")
        return {"status": "ok", "message": f"Ingest log for '{filename}' removed. Re-ingest to reload."}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/mis/purge-date/{date_str}", dependencies=[Depends(_require_admin)])
def purge_mis_date(date_str: str):
    """
    Delete all MIS records for a specific date (YYYY-MM-DD).
    Useful for re-uploading corrected data for a reporting date.
    """
    try:
        import datetime
        from src.infrastructure.persistence.mis_repository import MISRepository
        from src.infrastructure.persistence.sqlite_models import MISRecordModel

        try:
            target_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid date '{date_str}'. Use YYYY-MM-DD.")

        repo = MISRepository()
        session = repo.session_factory()
        deleted = session.query(MISRecordModel).filter(MISRecordModel.date == target_date).delete()
        session.commit()
        session.close()

        return {
            "status": "ok",
            "date": date_str,
            "records_deleted": deleted,
            "message": f"Purged {deleted} MIS records for {date_str}.",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ────────────────────────────────────────────────────────────────────────────
# MASTER DATA SYNC
# ────────────────────────────────────────────────────────────────────────────

@router.post("/master/sync/staff", dependencies=[Depends(_require_admin)])
def sync_staff():
    """
    Re-sync staff master from Staff.csv / Staff Details*.xlsx / StfData.csv.
    Upserts staff records, deactivates staff no longer in source.
    """
    try:
        from src.application.services.master_sync_service import MasterSyncService
        from src.infrastructure.persistence.master_repository import MasterRepository
        svc = MasterSyncService(MasterRepository())
        svc.sync_staff_from_csv()
        # Count staff after sync
        count = len(svc.repo.get_by_category("STAFF"))
        return {
            "status": "ok",
            "message": f"Staff sync complete. {count} staff records in master.",
            "staff_count": count,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/master/sync/units", dependencies=[Depends(_require_admin)])
def sync_units():
    """
    Re-sync branch units from branches.csv.
    Upserts unit records, deactivates units no longer in source.
    """
    try:
        from src.application.services.master_sync_service import MasterSyncService
        from src.infrastructure.persistence.master_repository import MasterRepository
        svc = MasterSyncService(MasterRepository())
        svc.sync_units_from_csv()
        count = len(svc.repo.get_by_category("UNIT"))
        return {
            "status": "ok",
            "message": f"Units sync complete. {count} branch units in master.",
            "unit_count": count,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/master/sync/departments", dependencies=[Depends(_require_admin)])
def sync_departments():
    """
    Re-sync departments from departments.csv.
    """
    try:
        from src.application.services.master_sync_service import MasterSyncService
        from src.infrastructure.persistence.master_repository import MasterRepository
        svc = MasterSyncService(MasterRepository())
        svc.sync_departments_from_csv()
        count = len(svc.repo.get_by_category("DEPT"))
        return {
            "status": "ok",
            "message": f"Departments sync complete. {count} departments in master.",
            "dept_count": count,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/master/sync/all", dependencies=[Depends(_require_admin)])
def sync_all_masters():
    """
    Run all three master syncs in sequence: units → staff → departments.
    """
    try:
        from src.application.services.master_sync_service import MasterSyncService
        from src.infrastructure.persistence.master_repository import MasterRepository
        svc = MasterSyncService(MasterRepository())
        svc.sync_units_from_csv()
        svc.sync_staff_from_csv()
        svc.sync_departments_from_csv()
        units = len(svc.repo.get_by_category("UNIT"))
        staff = len(svc.repo.get_by_category("STAFF"))
        depts = len(svc.repo.get_by_category("DEPT"))
        return {
            "status": "ok",
            "message": "Full master sync complete.",
            "unit_count": units,
            "staff_count": staff,
            "dept_count": depts,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ────────────────────────────────────────────────────────────────────────────
# MASTER STATS (quick summary for the admin dashboard)
# ────────────────────────────────────────────────────────────────────────────

@router.get("/stats", dependencies=[Depends(_require_admin)])
def get_admin_stats():
    """
    Return a quick summary of master data counts and MIS availability.
    Used to populate the admin dashboard header cards.
    """
    try:
        from src.infrastructure.persistence.master_repository import MasterRepository
        from src.infrastructure.persistence.mis_repository import MISRepository

        master_repo = MasterRepository()
        mis_repo = MISRepository()

        units  = len(master_repo.get_by_category("UNIT"))
        staff  = len(master_repo.get_by_category("STAFF"))
        depts  = len(master_repo.get_by_category("DEPT"))
        dates  = mis_repo.get_available_dates()

        session = mis_repo.session_factory()
        from sqlalchemy import text
        file_count = session.execute(text("SELECT COUNT(*) FROM ingested_files")).scalar()
        session.close()

        return {
            "unit_count":   units,
            "staff_count":  staff,
            "dept_count":   depts,
            "mis_dates":    len(dates),
            "mis_latest":   str(dates[-1]) if dates else None,
            "ingested_files": file_count or 0,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
