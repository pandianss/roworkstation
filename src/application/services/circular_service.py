import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class CircularService:
    def __init__(self, data_path="data/circulars.json"):
        self.data_path = data_path
        self._ensure_data_file()

    def _ensure_data_file(self):
        if not os.path.exists(self.data_path):
            with open(self.data_path, 'w', encoding="utf-8") as f:
                json.dump([], f)

    def _load_data(self) -> List[Dict]:
        with open(self.data_path, 'r', encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "circulars" in data:
                return data["circulars"]
            return data if isinstance(data, list) else []

    def _save_data(self, circulars: List[Dict]):
        with open(self.data_path, 'w', encoding="utf-8") as f:
            json.dump({"circulars": circulars}, f, indent=2, ensure_ascii=False)

    def generate_ref_no(self, region_code: str, dept_code: str) -> str:
        """Generate CIR/REGION/DEPT/SEQ ref number"""
        circulars = self._load_data()
        count = len(circulars) + 1
        seq = str(count).zfill(3)
        return f"CIR/{region_code}/{dept_code}/{seq}"

    def save_circular(self, circular: Dict):
        circulars = self._load_data()
        
        # Prevent exact duplicates within the same day/dept
        for c in circulars:
            if (c.get('subject') == circular.get('subject') and 
                c.get('date') == circular.get('date') and 
                c.get('dept') == circular.get('dept')):
                # Already exists, just return it
                return c

        if 'id' not in circular:
            # Use ref_no or number as id if available, else generate
            circular['id'] = circular.get('ref_no') or circular.get('number') or datetime.now().strftime("%Y%m%d%H%M%S")
        
        if 'created_at' not in circular:
            circular['created_at'] = datetime.now().isoformat()
        
        # Check if updating by ID
        updated = False
        for i, c in enumerate(circulars):
            if isinstance(c, dict) and c.get('id') == circular['id']:
                circulars[i] = circular
                updated = True
                break
        
        if not updated:
            circulars.append(circular)
            
        self._save_data(circulars)

        # Sync to Wizard Submissions so it shows up in Unified Master Archive
        try:
            from src.application.services.wizard_service import WizardService
            wiz_svc = WizardService()
            wiz_svc.save_submission(
                wizard_type="circular_drafter",
                submitted_by=circular.get('author', 'Staff'),
                content=circular,
                subject=circular.get('subject', 'Circular'),
                ref=circular.get('ref_no')
            )
        except Exception:
            pass

        return circular

    def get_all(self) -> List[Dict]:
        data = self._load_data()
        # Ensure only dicts are processed for sorting
        valid_data = [x for x in data if isinstance(x, dict)]
        return sorted(valid_data, key=lambda x: x.get('created_at', x.get('date', '')), reverse=True)

    def get_by_id(self, circ_id: str) -> Optional[Dict]:
        circulars = self._load_data()
        for c in circulars:
            if isinstance(c, dict) and (c.get('id') == circ_id or c.get('number') == circ_id or c.get('ref_no') == circ_id):
                return c
        return None

    def delete_circular(self, circ_id: str) -> bool:
        circulars = self._load_data()
        initial_count = len(circulars)
        circulars = [c for c in circulars if isinstance(c, dict) and c.get('id') != circ_id and c.get('number') != circ_id and c.get('ref_no') != circ_id]
        if len(circulars) < initial_count:
            self._save_data(circulars)

            # Delete from Wizard Submissions
            try:
                from src.infrastructure.persistence.database import get_db_session
                from src.infrastructure.persistence.sqlite_models import WizardSubmissionModel
                with get_db_session() as session:
                    sub = session.query(WizardSubmissionModel).filter(
                        (WizardSubmissionModel.reference_no == circ_id) | 
                        (WizardSubmissionModel.reference_no.like(f"%{circ_id}%"))
                    ).first()
                    if sub:
                        session.delete(sub)
                        session.commit()
            except Exception:
                pass

            return True
        return False
