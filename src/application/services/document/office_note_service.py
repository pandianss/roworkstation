from __future__ import annotations
import pandas as pd
import json
import os
import datetime
from typing import List, Dict, Any, Optional

class OfficeNoteService:
    def __init__(self, csv_path: str = "officeNote.csv"):
        self.csv_path = csv_path
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.csv_path):
            df = pd.DataFrame(columns=[
                "id", "type", "status", "titleEn", "contentJson", 
                "preparerId", "approverId", "createdAt", "updatedAt", 
                "previousVersionId", "version", "referenceNo", "scannedCopyUrl"
            ])
            df.to_csv(self.csv_path, index=False)

    def get_all(self) -> pd.DataFrame:
        if not os.path.exists(self.csv_path):
            return pd.DataFrame()
        df = pd.read_csv(self.csv_path)
        # Parse contentJson for easier use
        df['parsed_content'] = df['contentJson'].apply(lambda x: json.loads(x) if isinstance(x, str) else {})
        # Extract department for filtering/display
        df['dept'] = df['parsed_content'].apply(lambda x: x.get('deptName', 'Unknown'))
        return df

    def save_note(self, note_data: Dict[str, Any]):
        df = pd.read_csv(self.csv_path)
        
        now = datetime.datetime.now().isoformat()
        
        if 'id' not in note_data or not note_data['id']:
            import uuid
            note_data['id'] = str(uuid.uuid4())
            note_data['createdAt'] = now
            note_data['version'] = 1
        
        note_data['updatedAt'] = now
        
        # Prepare row for CSV
        row = {
            "id": note_data.get('id'),
            "type": note_data.get('type', 'CUSTOM'),
            "status": note_data.get('status', 'DRAFT'),
            "titleEn": note_data.get('titleEn', ''),
            "contentJson": json.dumps(note_data.get('parsed_content', {})),
            "preparerId": note_data.get('preparerId'),
            "approverId": note_data.get('approverId'),
            "createdAt": note_data.get('createdAt'),
            "updatedAt": note_data.get('updatedAt'),
            "previousVersionId": note_data.get('previousVersionId'),
            "version": note_data.get('version', 1),
            "referenceNo": note_data.get('referenceNo'),
            "scannedCopyUrl": note_data.get('scannedCopyUrl')
        }

        if row['id'] in df['id'].values:
            idx = df[df['id'] == row['id']].index[0]
            for key, val in row.items():
                df.at[idx, key] = val
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

        df.to_csv(self.csv_path, index=False)

        # Sync to Wizard Submissions so it shows up in Unified Master Archive
        try:
            from src.application.services.wizard_service import WizardService
            wiz_svc = WizardService()
            w_type = note_data.get('type', 'CUSTOM').lower()
            if w_type == 'custom':
                w_type = 'office_note'
            
            content = note_data.get('parsed_content', {})
            prep_name = content.get('signatorySnapshot', {}).get('preparer', {}).get('name', note_data.get('preparerId', 'Staff'))
            
            wiz_svc.save_submission(
                wizard_type=w_type,
                submitted_by=prep_name,
                content=content,
                subject=note_data.get('titleEn', 'Office Note'),
                ref=note_data.get('referenceNo')
            )
        except Exception:
            pass

        return note_data

    def delete_note(self, note_id: str):
        df = pd.read_csv(self.csv_path)
        if note_id not in df['id'].values:
            return False
        
        # Get info for re-sequencing before deletion
        note = df[df['id'] == note_id].iloc[0]
        ref = str(note['referenceNo'])
        
        # Delete
        df = df[df['id'] != note_id]
        df.to_csv(self.csv_path, index=False)

        # Delete from Wizard Submissions so the Unified Master Archive is kept in sync
        try:
            from src.infrastructure.persistence.database import get_db_session
            from src.infrastructure.persistence.sqlite_models import WizardSubmissionModel
            with get_db_session() as session:
                sub = session.query(WizardSubmissionModel).filter(
                    WizardSubmissionModel.reference_no == ref
                ).first()
                if sub:
                    session.delete(sub)
                    session.commit()
        except Exception:
            pass
        
        # Trigger re-sequencing if it follows the RO/DEPT/YEAR/MONTH/SEQ pattern
        if ref and ref.startswith("RO/"):
            parts = ref.split('/')
            if len(parts) >= 4:
                dept = parts[1]
                year = parts[2]
                month = parts[3]
                self.resequence(dept, year, month)
        
        return True

    def resequence(self, dept: str, year: str, month: str):
        """Adjusts reference numbers to fill gaps for a specific dept/period."""
        df = pd.read_csv(self.csv_path)
        
        # Pattern to match: RO/{dept}/{year}/{month}/...
        pattern = f"RO/{dept}/{year}/{month}/"
        
        # Filter notes that match the pattern
        mask = df['referenceNo'].str.startswith(pattern, na=False)
        subset = df[mask].copy()
        
        if subset.empty:
            return
        
        # Sort by createdAt to maintain original order
        subset = subset.sort_values('createdAt')
        
        for i, (idx, row) in enumerate(subset.iterrows(), 1):
            new_seq = str(i).zfill(2)
            new_ref = f"{pattern}{new_seq}"
            
            if row['referenceNo'] != new_ref:
                old_ref = row['referenceNo']
                df.at[idx, 'referenceNo'] = new_ref
                # Also update inside JSON if possible
                try:
                    content = json.loads(row['contentJson'])
                    # Try common keys
                    for k in ['referenceNo', 'refNo', 'ref_no', 'reference']:
                        if k in content:
                            content[k] = new_ref
                    df.at[idx, 'contentJson'] = json.dumps(content)
                except:
                    pass

                # Update in SQLite WizardSubmissions
                try:
                    from src.infrastructure.persistence.database import get_db_session
                    from src.infrastructure.persistence.sqlite_models import WizardSubmissionModel
                    with get_db_session() as session:
                        sub = session.query(WizardSubmissionModel).filter(
                            WizardSubmissionModel.reference_no == old_ref
                        ).first()
                        if sub:
                            sub.reference_no = new_ref
                            session.commit()
                except Exception:
                    pass
        
        df.to_csv(self.csv_path, index=False)

    def generate_next_reference(self, dept: str) -> str:
        """Generates the next sequential reference number for a department."""
        now = datetime.datetime.now()
        year = str(now.year)
        month = str(now.month).zfill(2)
        
        df = self.get_all()
        pattern = f"RO/{dept}/{year}/{month}/"
        
        if df.empty:
            return f"{pattern}01"
            
        subset = df[df['referenceNo'].str.startswith(pattern, na=False)]
        if subset.empty:
            return f"{pattern}01"
            
        # Extract sequence and find max
        def get_seq(ref):
            try: return int(ref.split('/')[-1])
            except: return 0
            
        max_seq = subset['referenceNo'].apply(get_seq).max()
        return f"{pattern}{str(max_seq + 1).zfill(2)}"
