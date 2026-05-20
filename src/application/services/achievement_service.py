import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class AchievementService:
    def __init__(self, data_path="data/achievements.json"):
        self.data_path = data_path
        self._ensure_data_file()

    def _ensure_data_file(self):
        # Ensure parent directory exists
        dir_name = os.path.dirname(self.data_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        if not os.path.exists(self.data_path):
            default_achievements = [
                {"id": "casa_excellence", "title": "CASA Excellence Award", "desc": "Ranked #1 in Zone for CASA growth in Q3.", "created_at": datetime.now().isoformat()},
                {"id": "digital_onboarding", "title": "Digital Onboarding", "desc": "100% Mobile Banking registration in 15 rural branches.", "created_at": datetime.now().isoformat()},
                {"id": "msme_support", "title": "MSME Support", "desc": "₹ 50Cr sanctioned to local textile units in Vedasandur.", "created_at": datetime.now().isoformat()}
            ]
            with open(self.data_path, 'w', encoding="utf-8") as f:
                json.dump({"achievements": default_achievements}, f, indent=2, ensure_ascii=False)

    def _load_data(self) -> List[Dict]:
        if not os.path.exists(self.data_path):
            self._ensure_data_file()
        try:
            with open(self.data_path, 'r', encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "achievements" in data:
                    return data["achievements"]
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_data(self, achievements: List[Dict]):
        with open(self.data_path, 'w', encoding="utf-8") as f:
            json.dump({"achievements": achievements}, f, indent=2, ensure_ascii=False)

    def get_all(self) -> List[Dict]:
        data = self._load_data()
        return [x for x in data if isinstance(x, dict)]

    def save_achievement(self, title: str, desc: str, ach_id: Optional[str] = None) -> Dict:
        achievements = self._load_data()
        if not ach_id:
            import re
            slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
            ach_id = f"ach_{slug}_{int(datetime.now().timestamp())}"
            
        new_ach = {
            "id": ach_id,
            "title": title,
            "desc": desc,
            "created_at": datetime.now().isoformat()
        }
        
        updated = False
        for i, a in enumerate(achievements):
            if a.get("id") == ach_id:
                achievements[i] = new_ach
                updated = True
                break
                
        if not updated:
            achievements.append(new_ach)
            
        self._save_data(achievements)
        return new_ach

    def delete_achievement(self, ach_id: str) -> bool:
        achievements = self._load_data()
        initial_count = len(achievements)
        achievements = [a for a in achievements if a.get("id") != ach_id]
        if len(achievements) < initial_count:
            self._save_data(achievements)
            return True
        return False
