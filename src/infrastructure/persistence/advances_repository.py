from __future__ import annotations
import pandas as pd
from sqlalchemy import create_engine, select, delete, func
from sqlalchemy.orm import sessionmaker
from src.infrastructure.persistence.sqlite_models import Base, AdvancesRecordModel
import os

class AdvancesRepository:
    def __init__(self, db_path="data/mis_store.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_records(self, df: pd.DataFrame, report_dt):
        """Save a dataframe of advances to SQLite. Overwrites existing for same date."""
        session = self.Session()
        try:
            # 1. Clean up existing records for this date
            session.execute(delete(AdvancesRecordModel).where(AdvancesRecordModel.report_dt == report_dt))
            session.commit()
            
            # 2. Bulk Insert using pandas (Optimized)
            # Map column names to model fields
            mapping = {
                'BRANCH_CODE': 'branch_code',
                'AC_NAME': 'ac_name',
                'FORACID': 'foracid',
                'SCHM_CODE': 'schm_code',
                'GL_SUB_CD': 'gl_sub_cd',
                'OPEN_DT_NORM': 'open_dt',
                'LIMIT_CR': 'limit_cr',
                'BALANCE_CR': 'balance_cr',
                'RISK_CATEGORY': 'risk_category',
                'L1_CATEGORY': 'l1_category',
                'L2_SECTOR': 'l2_sector',
                'L3_SCHEME': 'l3_scheme',
                'PRIORITY_TYPE': 'priority_type'
            }
            
            to_save = df[list(mapping.keys())].copy()
            to_save.rename(columns=mapping, inplace=True)
            
            # Ensure dates are pure date objects (no time component) for SQLite
            to_save['report_dt'] = report_dt
            if 'open_dt' in to_save.columns:
                to_save['open_dt'] = pd.to_datetime(to_save['open_dt']).dt.date
            
            # Use method='multi' for faster insertion if using standard sqlite, 
            # but for 160k rows, chunksize + default is usually safer/faster on some systems.
            to_save.to_sql('advances_records', con=self.engine, if_exists='append', index=False, chunksize=10000)
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_latest_date(self):
        session = self.Session()
        res = session.query(func.max(AdvancesRecordModel.report_dt)).scalar()
        session.close()
        return res

    def get_records_by_date(self, report_dt) -> pd.DataFrame:
        query = select(AdvancesRecordModel).where(AdvancesRecordModel.report_dt == report_dt)
        return pd.read_sql(query, con=self.engine)

    def get_available_dates(self):
        session = self.Session()
        res = session.query(AdvancesRecordModel.report_dt).distinct().all()
        session.close()
        return sorted([r[0] for r in res], reverse=True)
