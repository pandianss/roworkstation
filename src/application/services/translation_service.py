from __future__ import annotations

class SalutationMapper:
    """Helper to map gender to trilingual salutations."""
    MAPPINGS = {
        "M": {"en": "Shri.", "hi": "श्री", "ta": "திரு"},
        "F": {"en": "Smt.", "hi": "श्रीमती", "ta": "திருமதி"},
        "O": {"en": "Ms.", "hi": "सुश्री", "ta": "செல்வி"}
    }

    @classmethod
    def get_trilingual(cls, gender: str) -> dict:
        """Get dict with en, hi, ta salutations."""
        g = str(gender).upper().strip() if gender else "M"
        return cls.MAPPINGS.get(g, cls.MAPPINGS["M"])

class DesignationMapper:
    """Helper to map English designations to Hindi and Tamil."""
    MAPPINGS = {
        "SENIOR REGIONAL MANAGER": {"hi": "वरिष्ठ क्षेत्रीय प्रबंधक", "ta": "முதன்மை மண்டல மேலாளர்"},
        "CHIEF REGIONAL MANAGER": {"hi": "मुख्य क्षेत्रीय प्रबंधक", "ta": "தலைமை மண்டல மேலாளர்"},
        "REGIONAL MANAGER": {"hi": "क्षेत्रीय प्रबंधक", "ta": "மண்டல மேலாளர்"},
        "CHIEF MANAGER": {"hi": "मुख्य प्रबंधक", "ta": "முதன்மை மேலாளர்"},
        "SENIOR MANAGER": {"hi": "वरிஷ்ட प्रबंधक", "ta": "மூத்த மேலாளர்"},
        "ASST MANAGER": {"hi": "सहायक प्रबंधक", "ta": "உதவி மேலாளர்"},
        "ASSISTANT MANAGER": {"hi": "सहायक प्रबंधक", "ta": "உதவி மேலாளர்"},
        "MANAGER": {"hi": "प्रबंधक", "ta": "மேலாளர்"},
        "OFFICER": {"hi": "अधिकारी", "ta": "அதிகாரி"},
        "CUSTOMER SERVICE ASSOCIATE": {"hi": "ग्राहक सेवा सहयोगी", "ta": "வாடிக்கையாளர் சேவை உதவியாளர்"},
        "CSA": {"hi": "ग्राहक सेवा सहयोगी", "ta": "வாடிக்கையாளர் சேவை உதவியாளர்"},
        "PART TIME HOUSE KEEPER": {"hi": "अंशकालिक हाउस कीपर", "ta": "பகுதி நேர தூய்மை பணியாளர்"},
        "PTHK": {"hi": "अंशकालिक हाउस कीपर", "ta": "பகுதி நேர தூய்மை பணியாளர்"},
        "SWEEPER": {"hi": "सफाई कर्मचारी", "ta": "தூய்மை பணியாளர்"}
    }

    @classmethod
    def get_trilingual(cls, desig_en: str) -> dict:
        """Get dict with en, hi, ta designations with longest-match priority."""
        d_up = str(desig_en).upper().strip()
        
        # Sort keys by length descending to ensure longest match
        sorted_keys = sorted(cls.MAPPINGS.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            if key in d_up:
                trans = cls.MAPPINGS[key]
                return {"en": desig_en, "hi": trans["hi"], "ta": trans["ta"]}
        
        # Default fallback
        return {"en": desig_en, "hi": desig_en, "ta": desig_en}
