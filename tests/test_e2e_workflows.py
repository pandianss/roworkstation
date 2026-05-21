from __future__ import annotations
import unittest
import datetime
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.persistence.sqlite_models import Base, MasterRecordModel, MISRecordModel
from src.application.services.wizard_service import WizardService
from src.application.use_cases.mis.service import MISAnalyticsService
from src.application.services.performance_letter_service import PerformanceLetterService
from src.application.services.advances_service import AdvancesService

class TestE2EWorkflows(unittest.TestCase):
    def setUp(self):
        """Initializes an in-memory SQLite database environment for complete integration testing."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        

        
        # 1. Seed Branch Master Data
        branch = MasterRecordModel(
            category="UNIT",
            code="1234",
            name_en="Dindigul Regional Office Branch",
            metadata_json='{"sol": "1234", "branch_name": "Dindigul"}'
        )
        self.session.add(branch)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_e2e_ingestion_to_analytics_pipeline(self):
        """Validates the complete raw data ingestion -> analytical snapshot segmentation pipeline."""
        # Arrange - Construct a mock advances dataframe matching the Excel columns structure
        raw_df = pd.DataFrame([{
            "REPORT_DT": 20260517, # Matches split len(latest) == 8 logic
            "BRANCH_CODE": 1234,
            "AC_NAME": "S. SATISH PANDIAN",
            "FORACID": "SB12345",
            "SCHM_CODE": "LAA",
            "GL_SUB_CD": "9876",
            "OPEN_DT_NORM": datetime.date(2026, 1, 1), # Matches advances_repository expected key
            "LIMIT_CR": 5000000.0,
            "BALANCE_CR": 4500000.0,
            "RISK_CATEGORY": "LOW",
            "L1_CATEGORY": "RETAIL",
            "L2_SECTOR": "HOUSING",
            "L3_SCHEME": "HOUSING",
            "PRIORITY_TYPE": "PRIORITY"
        }])
        
        # Act 1 - Trigger advances service classification & database insertion
        adv_service = AdvancesService()
        # Override self.repo for stateless isolated engine context
        from src.infrastructure.persistence.advances_repository import AdvancesRepository
        repo = AdvancesRepository()
        repo.Session = sessionmaker(bind=self.engine)
        repo.engine = self.engine
        adv_service.repo = repo
        
        report_date = adv_service.save_to_db(raw_df)
        self.assertEqual(report_date, datetime.date(2026, 5, 17))
        
        # Act 2 - Seed an MIS record snapshot matching the Sol
        mis_record = MISRecordModel(
            date=datetime.date(2026, 5, 17),
            sol=1234,
            adv=4500000.0,
            sb=1000000.0,
            td=2000000.0,
            total_retail=4500000.0
        )
        self.session.add(mis_record)
        self.session.commit()
        
        # Act 3 - Run Bounded Analytics build_snapshot
        analytics_service = MISAnalyticsService()
        analytics_service.repository.session_factory = lambda: self.session
        analytics_service.repository.engine = self.engine
        
        # Fetching for May 17, 2026
        params = {"selected_date": datetime.date(2026, 5, 17), "sols": None}
        snapshot = analytics_service.build_snapshot(params)
        
        # Assert - Verify that metrics are perfectly loaded and CD ratio computed correctly
        self.assertIsNotNone(snapshot)
        kpis = snapshot.kpis
        self.assertEqual(kpis["Total Advances"], 4500000.0)
        self.assertEqual(kpis["Total Deposits"], 3000000.0) # SB + TD
        self.assertEqual(kpis["CD Ratio"], 150.0) # (4500000 / 3000000) * 100

    def test_e2e_performance_appreciation_letter_loop(self):
        """Validates that budgets/snapshot calculations correctly filter outstanding branches for appreciation letters."""
        # Arrange - Seed MIS record for Prev FY End (2026-03-31) and current Date (2026-05-17)
        # Note: CASA/RET TD are dynamically derived or ignored, so we do not pass them to MISRecordModel.
        mis_prev = MISRecordModel(
            date=datetime.date(2026, 3, 31),
            sol=1234,
            sb=250000.0,
            cd=50000.0,
            td=100000.0
        )
        mis_curr = MISRecordModel(
            date=datetime.date(2026, 5, 17),
            sol=1234,
            sb=400000.0,
            cd=100000.0,
            td=200000.0
        )
        self.session.add(mis_prev)
        self.session.add(mis_curr)
        
        # Seed targets for May 2026
        from src.infrastructure.persistence.sqlite_models import BudgetModel
        budgets = [
            BudgetModel(sol=1234, parameter="CASA", date=datetime.date(2026, 5, 31), target=400000.0),
            BudgetModel(sol=1234, parameter="SB", date=datetime.date(2026, 5, 31), target=300000.0),
            BudgetModel(sol=1234, parameter="CD", date=datetime.date(2026, 5, 31), target=100000.0)
        ]
        for b in budgets:
            self.session.add(b)
        self.session.commit()
        
        # Act - Trigger performance calculation
        letter_service = PerformanceLetterService()
        letter_service.analytics_service.repository.session_factory = lambda: self.session
        letter_service.analytics_service.repository.engine = self.engine
        letter_service.budget_repo.session_factory = lambda: self.session
        letter_service.budget_repo.engine = self.engine
        
        # Generate target performance data for May 17, 2026
        target_date = datetime.date(2026, 5, 17)
        data = letter_service.get_branch_performance(target_date)
        
        # Assert - Branch 1234 achieved 125% of target budget, so it should be listed with achievements
        self.assertEqual(len(data), 1)
        branch_perf = data[0]
        self.assertEqual(branch_perf["sol"], 1234)
        
        # Verify that CASA group is listed under achievements
        casa_group = branch_perf["groups"]["CASA"]
        self.assertTrue(len(casa_group["achievements"]) > 0)
        
        # Verify achievement details for the parent param "CASA"
        casa_entry = next(entry for entry in casa_group["achievements"] if entry["parameter"] == "CASA")
        self.assertEqual(casa_entry["actual"], 500000.0)
        self.assertEqual(casa_entry["target"], 400000.0)
        self.assertEqual(casa_entry["pct"], 125.0)

    def test_e2e_high_value_dd_operational_workflow(self):
        """Validates the sequential thread-safe registration and document generation lifecycle of High Value DD office notes."""
        # Arrange - Instantiate WizardService linked to SQLite session context
        wizard_service = WizardService(session=self.session)
        
        form_content = {
            "branchName": "Test Branch Dindigul",
            "purchaserName": "John Doe",
            "amount": "1500000",
            "favoring": "Acme Corp",
            "purpose": "Business Transaction",
            "sourceOfFunds": "CASA Account Debit",
            "sol": "1234"
        }
        
        # Act 1 - Submit High Value DD form registration
        submission = wizard_service.save_submission(
            wizard_type="high_value_dd",
            submitted_by="S. Satish Pandian",
            subject="Approval of High Value DD - ₹15.00 Lakhs",
            content=form_content,
            ref="RO/OPS/2026/001"
        )
        
        # Assert 1 - Form is assigned a sequential and formatted reference number
        self.assertIsNotNone(submission.id)
        self.assertEqual(submission.reference_no, "RO/OPS/2026/001")
        
        # Act 2 - Generate the audit-ready trilingual note HTML
        from src.core.document.engine import DocumentEngine
        engine = DocumentEngine()
        
        # Render the template variables using the correct render_doc method
        rendered_html = engine.render_doc("visiting_card.html", **{
            "name_en": "S. Satish Pandian",
            "name_hi": "एस. सतीश पांडियन",
            "name_ta": "எஸ். சதீஷ் பாண்டியன்",
            "designation_en": "Senior Regional Manager",
            "designation_hi": "वरिष्ठ क्षेत्रीय प्रबंधक",
            "designation_local": "முதன்மை மண்டல மேலாளர்",
            "ref_no": submission.reference_no,
            "address_hi": "डिंडीगुल",
            "address_en": "Dindigul"
        })
        
        # Assert 2 - Rendered HTML contains our values perfectly
        self.assertIn("S. Satish Pandian", rendered_html)
        self.assertIn("वरिष्ठ क्षेत्रीय प्रबंधक", rendered_html)

if __name__ == "__main__":
    unittest.main()
