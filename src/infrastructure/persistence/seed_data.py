from __future__ import annotations

import json
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.persistence.sqlite_models import Base, MasterRecordModel
from src.core.paths import project_path

def seed_master_data():
    db_path = project_path("data", "mis_store.db")
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Seed Units
        units_path = project_path("data", "units.csv")
        if not units_path.exists():
             # Fallback to root if not in data/
             units_path = project_path().parent / "units.csv"
        
        if units_path.exists():
            print(f"Importing units from {units_path}")
            df_units = pd.read_csv(units_path)
            for _, row in df_units.iterrows():
                # Check if exists
                exists = session.query(MasterRecordModel).filter_by(category="UNIT", code=str(row['code'])).first()
                if not exists:
                    record = MasterRecordModel(
                        category="UNIT",
                        code=str(row['code']),
                        name_en=row['nameEn'],
                        name_hi=row.get('nameHi'),
                        name_local=row.get('nameTa'),
                        metadata_json=json.dumps({
                            "type": row.get('type'),
                            "populationGroup": row.get('populationGroup'),
                            "district": row.get('district'),
                            "pincode": row.get('pincode')
                        })
                    )
                    session.add(record)
        
        # 2. Seed Staff
        staff_path = project_path("data", "Staff2.csv")
        if staff_path.exists():
            print(f"Importing staff from {staff_path}")
            df_staff = pd.read_csv(staff_path)
            for _, row in df_staff.iterrows():
                exists = session.query(MasterRecordModel).filter_by(category="STAFF", code=str(row['Roll'])).first()
                if not exists:
                    record = MasterRecordModel(
                        category="STAFF",
                        code=str(row['Roll']),
                        name_en=row['Name'],
                        metadata_json=json.dumps({
                            "designation": row.get('Designation'),
                            "grade": row.get('Grade'),
                            "sol": str(row.get('SOL'))
                        })
                    )
                    session.add(record)
        
        # 3. Seed Departments
        depts = [
            ("FI", "Financial Inclusion"),
            ("PLAN", "Planning"),
            ("ARID", "Agri & Rural Infra"),
            ("HRDD", "Human Resources"),
            ("GAD", "General Administration"),
            ("CRMD", "Credit Monitoring"),
            ("COM", "Compliance"),
            ("MKT", "Marketing"),
            ("LAW", "Law"),
            ("INS", "Inspection"),
            ("RSK", "Risk Management"),
            ("SME", "MSME"),
            ("RET", "Retail"),
            ("RCC", "Regional Computer Centre")
        ]
        for code, name in depts:
            exists = session.query(MasterRecordModel).filter_by(category="DEPARTMENT", code=code).first()
            if not exists:
                record = MasterRecordModel(
                    category="DEPARTMENT",
                    code=code,
                    name_en=name,
                    is_active=True
                )
                session.add(record)

        session.commit()
        print("Master data seeded successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error seeding master data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_master_data()
