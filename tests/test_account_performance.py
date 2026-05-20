import unittest
import datetime
from src.application.services.account_performance_service import AccountPerformanceService
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.sqlite_models import AccountOpeningModel, AccountClosureModel, MasterRecordModel

class AccountPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.service = AccountPerformanceService()
        
        # Clean test database records before each test
        with get_db_session() as session:
            session.query(AccountOpeningModel).delete()
            session.query(AccountClosureModel).delete()
            session.query(MasterRecordModel).filter(MasterRecordModel.category == "HOLIDAY").delete()
            session.commit()

    def test_calculate_working_days_april_2026(self):
        # April 2026:
        # Total days: 30
        # Sundays: April 5, 12, 19, 26 (4 days)
        # Saturdays: 
        #   - April 4 (1st Sat - working)
        #   - April 11 (2nd Sat - holiday)
        #   - April 18 (3rd Sat - working)
        #   - April 25 (4th Sat - holiday)
        # Expected working days: 30 - 4 Sundays - 2 holidays = 24 working days
        start_date = datetime.date(2026, 4, 1)
        end_date = datetime.date(2026, 4, 30)
        
        working_days = self.service.calculate_working_days(start_date, end_date, exclude_2nd_4th_sat=True)
        self.assertEqual(working_days, 24)

        # If Saturdays are not excluded
        working_days_no_sat = self.service.calculate_working_days(start_date, end_date, exclude_2nd_4th_sat=False)
        self.assertEqual(working_days_no_sat, 26)

    def test_public_holidays_calendar(self):
        start_date = datetime.date(2026, 4, 1)
        end_date = datetime.date(2026, 4, 30)

        # Add a public holiday on April 1 (Wednesday, normally working)
        self.service.add_public_holiday(datetime.date(2026, 4, 1), "Test Holiday")
        
        # Working days should decrement by 1 (24 -> 23)
        working_days = self.service.calculate_working_days(start_date, end_date, exclude_2nd_4th_sat=True)
        self.assertEqual(working_days, 23)

        # Retrieve holidays list
        holidays = self.service.get_public_holidays()
        self.assertEqual(len(holidays), 1)
        self.assertEqual(holidays[0]["date"], "2026-04-01")
        self.assertEqual(holidays[0]["name"], "Test Holiday")

        # Delete the holiday and verify working days are back to 24
        self.service.delete_public_holiday("2026-04-01")
        working_days_after_delete = self.service.calculate_working_days(start_date, end_date, exclude_2nd_4th_sat=True)
        self.assertEqual(working_days_after_delete, 24)

    def test_csv_ingestion_and_performance_calculation(self):
        # 1. Ingest Mock Openings CSV
        # SOL_ID,SCHM_TYPE,SCHM_CODE,ACCT_OPN_DATE,CLR_BAL_AMT,AVERAGE BALANCE
        open_csv_data = (
            "SOL_ID,SCHM_TYPE,SCHM_CODE,ACCT_OPN_DATE,CLR_BAL_AMT,AVERAGE BALANCE\n"
            "911,SBA,SBCRP,02.04.2026,680,2290.638298\n"   # Under SBA threshold (680 < 1000)
            "911,SBA,SBBSB,02.04.2026,83620,64123.95745\n" # Valid SBA (83620)
            "911,CAA,CAREG,02.04.2026,500,20000.0\n"       # Under CAA threshold (500 < 5000)
            "911,CAA,CAPUB,02.04.2026,12000,15000.0\n"     # Valid CAA (12000)
            "1001,SBA,SBLTS,03.04.2026,1500,1300.0\n"      # Valid SBA (1500)
        ).encode("utf-8")

        stats_open = self.service.import_openings_csv(open_csv_data)
        self.assertEqual(stats_open["count"], 5)
        self.assertEqual(set(stats_open["dates"]), {"2026-04-02", "2026-04-03"})

        # 2. Ingest Mock Closures CSV
        # SOL_ID,ACCT_CLS_DATE,SCHM_TYPE
        close_csv_data = (
            "SOL_ID,ACCT_CLS_DATE,SCHM_TYPE\n"
            "911,02.04.2026,SBA\n"  # 1 SBA closure for 911
            "911,02.04.2026,CAA\n"  # 1 CAA closure for 911
        ).encode("utf-8")

        stats_close = self.service.import_closures_csv(close_csv_data)
        self.assertEqual(stats_close["count"], 2)
        self.assertEqual(stats_close["dates"], ["2026-04-02"])

        # 3. Calculate Performance for April 2-3, 2026
        # Working days for April 2-3:
        # April 2: Thursday (working day)
        # April 3: Friday (working day)
        # Working days = 2.
        
        perf = self.service.get_performance_data(
            start_date=datetime.date(2026, 4, 2),
            end_date=datetime.date(2026, 4, 3),
            sba_thresholds={"RURAL": 1000.0, "SEMI URBAN": 1000.0, "URBAN": 1000.0},
            caa_thresholds={"RURAL": 5000.0, "SEMI URBAN": 10000.0, "URBAN": 10000.0},
            threshold_field="clr_bal_amt"
        )

        summary = perf["summary"]
        self.assertEqual(summary["sba_opened"], 3)
        self.assertEqual(summary["sba_low_bal"], 1)
        self.assertEqual(summary["sba_closed"], 1)
        # Net SBA = 3 opened - 1 low balance - 1 closed = 1
        self.assertEqual(summary["sba_net"], 1)
        self.assertEqual(summary["working_days"], 2)
        # SBA daily run rate = 1 / 2 = 0.5
        self.assertEqual(summary["sba_run_rate"], 0.5)

        self.assertEqual(summary["caa_opened"], 2)
        self.assertEqual(summary["caa_low_bal"], 1)
        self.assertEqual(summary["caa_closed"], 1)
        # Net CD/CAA = 2 opened - 1 low balance - 1 closed = 0
        self.assertEqual(summary["caa_net"], 0)
        self.assertEqual(summary["caa_run_rate"], 0.0)

        # Verify branch 911 specific values (Kalwarpatti - RURAL)
        branch_911 = next(b for b in perf["branches"] if b["sol"] == 911)
        self.assertEqual(branch_911["sba_opened"], 2)
        self.assertEqual(branch_911["sba_low_bal"], 1)
        self.assertEqual(branch_911["sba_closed"], 1)
        self.assertEqual(branch_911["sba_net"], 0)
        self.assertEqual(branch_911["sba_run_rate"], 0.0)

        # Verify branch 1001 specific values (URBAN)
        branch_1001 = next(b for b in perf["branches"] if b["sol"] == 1001)
        self.assertEqual(branch_1001["sba_opened"], 1)
        self.assertEqual(branch_1001["sba_low_bal"], 0)
        self.assertEqual(branch_1001["sba_closed"], 0)
        self.assertEqual(branch_1001["sba_net"], 1)
        self.assertEqual(branch_1001["sba_run_rate"], 0.5)

    def test_branch_type_threshold_differentiation(self):
        # Ingest openings
        # SOL 911 is RURAL
        # SOL 1830 is URBAN
        # Both open an SBA account with balance = 1500
        open_csv_data = (
            "SOL_ID,SCHM_TYPE,SCHM_CODE,ACCT_OPN_DATE,CLR_BAL_AMT,AVERAGE BALANCE\n"
            "911,SBA,SBCRP,02.04.2026,1500,1500.0\n"
            "1830,SBA,SBLTS,02.04.2026,1500,1500.0\n"
        ).encode("utf-8")
        self.service.import_openings_csv(open_csv_data)

        # Case A: rural threshold is 1000, urban threshold is 2000.
        # Rural account (1500 >= 1000) -> valid (low bal = 0)
        # Urban account (1500 < 2000) -> low balance (low bal = 1)
        perf = self.service.get_performance_data(
            start_date=datetime.date(2026, 4, 2),
            end_date=datetime.date(2026, 4, 2),
            sba_thresholds={"RURAL": 1000.0, "URBAN": 2000.0},
            threshold_field="clr_bal_amt"
        )
        
        branch_911 = next(b for b in perf["branches"] if b["sol"] == 911)
        branch_1830 = next(b for b in perf["branches"] if b["sol"] == 1830)

        self.assertEqual(branch_911["sba_low_bal"], 0)
        self.assertEqual(branch_1830["sba_low_bal"], 1)
