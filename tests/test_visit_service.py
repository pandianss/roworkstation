from __future__ import annotations
import unittest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.persistence.sqlite_models import Base, MasterRecordModel
from src.application.services.visit_service import VisitService

class TestVisitService(unittest.TestCase):
    def setUp(self):
        """Provides an isolated, in-memory SQLite database for testing."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
        # Pre-seed master records required by unit validation
        branch = MasterRecordModel(
            category="UNIT",
            code="1234",
            name_en="Test Branch Dindigul",
            metadata={"sol": "1234"}
        )
        self.session.add(branch)
        self.session.commit()
        
        self.service = VisitService(session=self.session)

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_add_visit_resolves_branch_name(self):
        visit_date = datetime.date(2026, 5, 17)
        
        # Act
        visit = self.service.add_visit(
            sol=1234,
            visit_date=visit_date,
            visitor_name="S. Satish Pandian",
            observations="Excellent progress in CASA acquisition.",
            advice="Maintain growth momentum."
        )
        
        # Assert
        self.assertIsNotNone(visit.id)
        self.assertEqual(visit.branch_name, "Test Branch Dindigul")  # Successfully resolved from MasterRecord
        self.assertEqual(visit.visitor_name, "S. Satish Pandian")
        self.assertEqual(visit.visit_date, visit_date)

    def test_get_monthly_visits(self):
        # Arrange
        # Log two distinct monthly visits
        self.service.add_visit(1234, datetime.date(2026, 5, 10), "RM", "Obs 1", "Advice 1")
        self.service.add_visit(1234, datetime.date(2026, 6, 15), "RM", "Obs 2", "Advice 2")
        
        # Act - Fetch for May 2026
        may_visits = self.service.get_monthly_visits(2026, 5)
        
        # Assert
        self.assertEqual(len(may_visits), 1)
        self.assertEqual(may_visits[0].observations, "Obs 1")

if __name__ == "__main__":
    unittest.main()
