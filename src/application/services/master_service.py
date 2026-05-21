from __future__ import annotations
import datetime
import os
import json
import logging
import pandas as pd
from src.core.paths import project_path
from src.core.config.config_loader import get_app_settings
from src.application.services.translation_service import SalutationMapper, DesignationMapper
from src.application.services.master_sync_service import MasterSyncService
from src.application.services.master_data_service import MasterDataService
from src.infrastructure.persistence.master_repository import MasterRepository
from src.domain.models.master import MasterRecord

logger = logging.getLogger(__name__)

class MasterService:
    def __init__(self, repo: MasterRepository | None = None) -> None:
        self.repo = repo or MasterRepository()
        self.sync_service = MasterSyncService(self.repo)
        self.data_service = MasterDataService(self.repo)
        self.settings = get_app_settings()

    def get_by_category(self, category: str) -> list[MasterRecord]:
        """Returns all records for a given category (STAFF, UNIT, DEPT). Freshly queried for real-time consistency."""
        return self.repo.get_by_category(category)

    # Delegated Data Methods
    def get_units_frame(self) -> pd.DataFrame:
        return self.data_service.get_units_frame()

    def get_departments_frame(self) -> pd.DataFrame:
        return self.data_service.get_departments_frame()

    def get_staff_frame(self) -> pd.DataFrame:
        return self.data_service.get_staff_frame()

    # Delegated Sync Methods
    def sync_staff_from_csv(self) -> None:
        self.sync_service.sync_staff_from_csv()
        self._update_sync_state()

    def sync_units_from_csv(self) -> None:
        self.sync_service.sync_units_from_csv()

    def sync_departments_from_csv(self) -> None:
        self.sync_service.sync_departments_from_csv()

    def update_master_file(self, category: str, file_bytes: bytes, filename: str) -> bool:
        """Saves uploaded file to the appropriate location and triggers sync."""
        target_map = {
            "STAFF": project_path("files", "Staff.csv"),
            "UNIT": project_path("files", "branches.csv"),
            "DEPT": project_path("files", "departments.csv"),
            "BUDGET": project_path("files", "Budget3.csv")
        }
        
        target_path = target_map.get(category.upper())
        if not target_path: return False
        
        # Backup existing
        if target_path.exists():
            backup_path = target_path.with_suffix(f".bak_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.rename(target_path, backup_path)
            
        with open(target_path, "wb") as f:
            f.write(file_bytes)
            
        # Trigger appropriate sync
        if category.upper() == "STAFF": self.sync_staff_from_csv()
        elif category.upper() == "UNIT": self.sync_units_from_csv()
        elif category.upper() == "DEPT": self.sync_departments_from_csv()
        
        self._update_sync_state()
        return True

    def sync_if_needed(self, force: bool = False) -> None:
        state_path = project_path("data", "master_sync.json")
        state = {}
        if state_path.exists():
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Ignoring unreadable master sync state %s: %s", state_path, exc)
                state = {}
        
        files = {
            "staff_csv": project_path("files", "Staff.csv"),
            "branches": project_path("files", "branches.csv"),
            "departments": project_path("files", "departments.csv")
        }
        
        needs_sync = force or not state_path.exists()
        for key, path in files.items():
            if not path.exists(): continue
            mtime = os.path.getmtime(path)
            if state.get(key) != mtime:
                needs_sync = True
                state[key] = mtime
        
        if needs_sync:
            logger.info("Syncing master data...")
            self.sync_units_from_csv()
            self.sync_staff_from_csv()
            self.sync_departments_from_csv()
            self._update_sync_state(state, files)

    def _update_sync_state(self, state: dict | None = None, files: dict | None = None) -> None:
        state_path = project_path("data", "master_sync.json")
        if state is None:
            state = {"last_sync": str(datetime.datetime.now())}
        else:
            state["last_sync"] = str(datetime.datetime.now())
            if files:
                for key, path in files.items():
                    if path.exists(): state[key] = os.path.getmtime(path)
        
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)

    # Unit Management Logic
    def update_unit_authorities(self, code: str, head_roll: str | None, second_roll: str | None, eff_date: str) -> bool:
        units = self.repo.get_by_category("UNIT")
        target_code = str(code).zfill(4)
        unit = next((u for u in units if str(u.code).zfill(4) == target_code), None)
        if not unit: return False
        
        meta = unit.metadata or {}
        meta["headUserId"] = head_roll if head_roll else ""
        meta["secondLineUserId"] = second_roll if second_roll else ""
        meta["authority_from"] = eff_date
        unit.metadata = meta
        self.repo.save(unit)
        
        try:
            self._write_back_to_branches_csv()
        except Exception as e:
            logger.warning(f"Failed to update branches.csv: {e}")
            
        self._update_sync_state()
        return True

    def update_unit_details(self, code: str, name_en: str, name_hi: str, name_ta: str, district: str, population_group: str, size: str, address1_en: str = "", address2_en: str = "", address3_en: str = "", address1_hi: str = "", address2_hi: str = "", address3_hi: str = "", address1_ta: str = "", address2_ta: str = "", address3_ta: str = "", pincode: str = "", email: str = "", phone: str = "") -> bool:
        units = self.repo.get_by_category("UNIT")
        target_code = str(code).zfill(4)
        unit = next((u for u in units if str(u.code).zfill(4) == target_code), None)
        if not unit: return False
        
        unit.name_en = name_en
        unit.name_hi = name_hi
        unit.name_local = name_ta
        
        meta = unit.metadata or {}
        meta["district"] = district
        meta["populationGroup"] = population_group
        meta["population_group"] = population_group
        meta["size"] = size
        
        # Strip floats or clean pincode, email, phone
        try:
            pincode_clean = str(pincode).strip()
            if pincode_clean.endswith(".0"):
                pincode_clean = pincode_clean[:-2]
            elif pincode_clean.lower() in ["nan", "none"]:
                pincode_clean = ""
            pincode = pincode_clean
        except:
            pass
        meta["pincode"] = pincode
        
        try:
            phone_clean = str(phone).strip()
            if phone_clean.endswith(".0"):
                phone_clean = phone_clean[:-2]
            elif phone_clean.lower() in ["nan", "none"]:
                phone_clean = ""
            phone = phone_clean
        except:
            pass
        meta["phone"] = phone
        
        try:
            email_clean = str(email).strip()
            if email_clean.lower() in ["nan", "none"]:
                email_clean = ""
            email = email_clean
        except:
            pass
        meta["email"] = email
        
        meta["address1_en"] = address1_en
        meta["address2_en"] = address2_en
        meta["address3_en"] = address3_en
        
        meta["address1_hi"] = address1_hi
        meta["address2_hi"] = address2_hi
        meta["address3_hi"] = address3_hi
        
        meta["address1_ta"] = address1_ta
        meta["address2_ta"] = address2_ta
        meta["address3_ta"] = address3_ta
        
        # Build multiline address fields dynamically
        meta["address"] = "\n".join([p for p in [address1_en, address2_en, address3_en] if p])
        meta["addressHi"] = "\n".join([p for p in [address1_hi, address2_hi, address3_hi] if p])
        meta["addressTa"] = "\n".join([p for p in [address1_ta, address2_ta, address3_ta] if p])
        
        unit.metadata = meta
        self.repo.save(unit)
        
        try:
            self._write_back_to_branches_csv()
        except Exception as e:
            logger.warning(f"Failed to update branches.csv: {e}")
            
        self._update_sync_state()
        return True

    def _write_back_to_branches_csv(self) -> None:
        csv_path = project_path("files", "branches.csv")
        records = self.repo.get_by_category("UNIT")
        data = []
        for r in records:
            meta = r.metadata or {}
            data.append({
                "id": r.id,
                "sNo": meta.get("sNo", ""),
                "code": r.code,
                "officeId": meta.get("officeId", ""),
                "nameEn": r.name_en,
                "nameTa": r.name_local,
                "nameHi": r.name_hi,
                "type": meta.get("type", "Branch"),
                "openDate": meta.get("openDate", ""),
                "district": meta.get("district", ""),
                "populationGroup": meta.get("populationGroup", ""),
                "riskCategory": meta.get("riskCategory", ""),
                "riskEffectiveDate": meta.get("riskEffectiveDate", ""),
                "specialStatus": meta.get("specialStatus", ""),
                "ifsc": meta.get("ifsc", ""),
                "address": meta.get("address", ""),
                "latitude": meta.get("latitude", ""),
                "longitude": meta.get("longitude", ""),
                "pincode": meta.get("pincode", ""),
                "headUserId": meta.get("headUserId", ""),
                "secondLineUserId": meta.get("secondLineUserId", ""),
                "addressHi": meta.get("addressHi", ""),
                "addressTa": meta.get("addressTa", ""),
                "email": meta.get("email", ""),
                "phone": meta.get("phone", ""),
                "size": meta.get("size", ""),
                "address1_en": meta.get("address1_en", ""),
                "address2_en": meta.get("address2_en", ""),
                "address3_en": meta.get("address3_en", ""),
                "address1_hi": meta.get("address1_hi", ""),
                "address2_hi": meta.get("address2_hi", ""),
                "address3_hi": meta.get("address3_hi", ""),
                "address1_ta": meta.get("address1_ta", ""),
                "address2_ta": meta.get("address2_ta", ""),
                "address3_ta": meta.get("address3_ta", "")
            })
        
        df = pd.DataFrame(data)
        original_cols = [
            "id", "sNo", "code", "officeId", "nameEn", "nameTa", "nameHi", "type", "openDate",
            "district", "populationGroup", "riskCategory", "riskEffectiveDate", "specialStatus",
            "ifsc", "address", "latitude", "longitude", "pincode", "headUserId", "secondLineUserId",
            "addressHi", "addressTa", "email", "phone", "size",
            "address1_en", "address2_en", "address3_en",
            "address1_hi", "address2_hi", "address3_hi",
            "address1_ta", "address2_ta", "address3_ta"
        ]
        df = df[original_cols]
        
        temp_path = csv_path.with_suffix(".tmp")
        df.to_csv(temp_path, index=False)
        if csv_path.exists():
            os.replace(temp_path, csv_path)
        else:
            os.rename(temp_path, csv_path)

    # Staff Management Logic
    def get_ro_executives(self) -> list[dict[str, str]]:
        staff = self.get_by_category("STAFF")
        execs = []
        region_code = self.settings.region_code
        for s in staff:
            meta = s.metadata or {}
            if str(meta.get("sol")) == region_code:
                grade = meta.get("grade", "")
                desig = meta.get("designation", "").upper()
                
                # Check explicit grade first
                is_exec = any(g in grade for g in ["MM II", "MM III", "SM IV", "SM V", "TEG VI", "TEG VII"])
                
                # Fallback to designation keywords if grade is missing
                if not grade or grade.strip() == "":
                    if any(kw in desig for kw in ["MANAGER", "CHIEF", "REGIONAL", "AGM", "DGM", "GM"]):
                        if "ASST" not in desig and "ASSISTANT" not in desig:
                            is_exec = True
                
                if is_exec:
                    execs.append({"roll": s.code, "name": s.name_en})
        return sorted(execs, key=lambda x: x["name"])

    def allot_staff_to_departments(self, roll: str, dept_codes: list[str]) -> bool:
        staff = next((r for r in self.repo.get_by_category("STAFF") if r.code == roll), None)
        if not staff: return False
        meta = staff.metadata or {}
        meta["departments"] = dept_codes
        staff.metadata = meta
        self.repo.save(staff)
        return True

    def update_staff_details(self, roll: str, name_hi: str, name_ta: str, sol: str, desig: str, gender: str, p_from: str, p_to: str) -> bool:
        staff_list = self.repo.get_by_category("STAFF")
        staff = next((s for s in staff_list if s.code == roll), None)
        if not staff: return False
        
        staff.name_hi = name_hi
        staff.name_local = name_ta
        meta = staff.metadata or {}
        
        if meta.get("sol") != sol or meta.get("designation") != desig:
            history = meta.get("postings", [])
            history.append({
                "sol": meta.get("sol"),
                "designation": meta.get("designation"),
                "from": meta.get("posting_from"),
                "to": datetime.date.today().strftime("%d.%m.%Y")
            })
            meta["postings"] = history
            
        tr_desig = DesignationMapper.get_trilingual(desig)
        meta.update({
            "sol": sol, "designation": desig,
            "desig_en": tr_desig["en"], "desig_hi": tr_desig["hi"], "desig_ta": tr_desig["ta"],
            "posting_from": p_from, "posting_to": p_to, "gender": gender
        })
        staff.metadata = meta
        self.repo.save(staff)
        
        try:
            self._write_back_to_staff_csv()
        except Exception as e:
            logger.warning(f"Failed to update Staff.csv: {e}")
        return True

    def _write_back_to_staff_csv(self) -> None:
        csv_path = project_path("files", "Staff.csv")
        df = self.get_staff_frame()
        # Staged write to prevent data loss
        temp_path = csv_path.with_suffix(".tmp")
        df.to_csv(temp_path, index=False)
        if csv_path.exists():
            os.replace(temp_path, csv_path)
        else:
            os.rename(temp_path, csv_path)

    def get_branch_manager(self, sol: str) -> dict:
        staff = self.repo.get_by_category("STAFF")
        units = self.repo.get_by_category("UNIT")
        target_sol = str(sol).zfill(4)
        
        manager = None
        unit = next((u for u in units if str(u.code).zfill(4) == target_sol), None)
        if unit:
            u_meta = unit.metadata or {}
            head_roll = u_meta.get("headUserId")
            if head_roll:
                manager = next((s for s in staff if str(s.code) == str(head_roll)), None)

        if not manager:
            for s in staff:
                meta = s.metadata or {}
                if str(meta.get("sol")).zfill(4) == target_sol and meta.get("status") == "BH":
                    manager = s
                    break
        
        if manager:
            meta = manager.metadata or {}
            sal = SalutationMapper.get_trilingual(meta.get("gender", "M"))
            tr_desig = DesignationMapper.get_trilingual(meta.get("designation", "Branch Manager"))
            return {
                "name": manager.name_en, "name_hi": manager.name_hi or manager.name_en, "name_ta": manager.name_local or manager.name_en,
                "sal_en": sal["en"], "sal_hi": sal["hi"], "sal_ta": sal["ta"],
                "designation": tr_desig["en"], "desig_en": tr_desig["en"], "desig_hi": tr_desig["hi"], "desig_ta": tr_desig["ta"],
                "grade": meta.get("grade"), "roll": manager.code
            }
        
        return {
            "name": "The Branch Manager", "name_hi": "शाखा प्रबंधक", "name_ta": "கிளை மேலாளர்",
            "sal_en": "The", "sal_hi": "माननीय", "sal_ta": "மதிப்பிற்குரிய",
            "designation": "Branch Manager", "desig_en": "Branch Manager", "desig_hi": "शाखा प्रबंधक", "desig_ta": "கிளை மேலாளர்",
            "grade": "N/A", "roll": "00000"
        }
