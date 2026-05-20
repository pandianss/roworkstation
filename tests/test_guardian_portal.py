from __future__ import annotations

import os
import unittest
import tempfile
from datetime import datetime

from src.application.services.guardian_service import GuardianService
from src.application.services.admin_service import AdminService
from src.application.services.document.service import DocumentService
from src.infrastructure.persistence.json_repo import JsonRepository


class TestGuardianPortal(unittest.TestCase):
    def setUp(self):
        """Provides isolated temporary JSON repositories for guardian tasks, followups, and users."""
        self.temp_followups = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_followups.write(b"[]")
        self.temp_followups.close()
        
        self.temp_tasks = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_tasks.write(b"[]")
        self.temp_tasks.close()
        
        self.temp_users = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_users.write(b"[]")
        self.temp_users.close()
        
        self.service = GuardianService()
        self.service.repo = JsonRepository(self.temp_followups.name, [])
        self.service.tasks_repo = JsonRepository(self.temp_tasks.name, [])
        
        self.admin_service = AdminService()
        self.admin_service.repo = JsonRepository(self.temp_users.name, [])

    def tearDown(self):
        """Clean up the temporary files."""
        if os.path.exists(self.temp_followups.name):
            os.unlink(self.temp_followups.name)
        if os.path.exists(self.temp_tasks.name):
            os.unlink(self.temp_tasks.name)
        if os.path.exists(self.temp_users.name):
            os.unlink(self.temp_users.name)

    def test_record_structured_followup(self):
        # Act
        followup = self.service.record_followup(
            go_username="test_officer",
            sol="1234",
            details="Branch lacks staff for NPA recovery.",
            category="NPA Recovery",
            status="PENDING_BRANCH",
            priority="P1"
        )
        
        # Assert
        self.assertEqual(followup.go_username, "test_officer")
        self.assertEqual(followup.sol, "1234")
        self.assertEqual(followup.details, "Branch lacks staff for NPA recovery.")
        self.assertEqual(followup.category, "NPA Recovery")
        self.assertEqual(followup.status, "PENDING_BRANCH")
        self.assertEqual(followup.priority, "P1")

    def test_create_and_list_daily_tasks(self):
        # Act
        task = self.service.create_daily_task(
            posted_by="test_rm",
            title="Drive CASA Campaigns",
            description="All branches must open at least 5 savings bank accounts today."
        )
        
        # Assert
        self.assertIsNotNone(task.id)
        self.assertEqual(task.posted_by, "test_rm")
        self.assertEqual(task.title, "Drive CASA Campaigns")
        
        # Act 2 - List today's tasks
        today_str = datetime.now().strftime("%d.%m.%Y")
        tasks = self.service.list_daily_tasks(date_str=today_str)
        
        # Assert 2
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, task.id)

    def test_compile_daily_report(self):
        today_str = datetime.now().strftime("%d.%m.%Y")
        
        # Arrange - Seed a task and a followup
        self.service.create_daily_task("rm_officer", "CASA Day", "Mobilize CASA accounts.")
        self.service.record_followup(
            go_username="go_officer",
            sol="1234",
            details="Observations in gold loan growth.",
            category="Gold Loan Growth",
            status="RESOLVED",
            priority="P2"
        )
        
        # Act
        report = self.service.compile_daily_report(today_str)
        
        # Assert
        self.assertEqual(report["date"], today_str)
        self.assertEqual(len(report["directives"]), 1)
        self.assertEqual(report["directives"][0]["title"], "CASA Day")
        self.assertEqual(len(report["followups"]), 1)
        self.assertEqual(report["followups"][0]["details"], "Observations in gold loan growth.")
        self.assertEqual(report["followups"][0]["category"], "Gold Loan Growth")

    def test_generate_daily_guardian_digest_html(self):
        today_str = datetime.now().strftime("%d.%m.%Y")
        
        # Arrange - Seed data in production path mock / patch temporarily
        doc_service = DocumentService()
        
        # Act - Render document HTML template
        html = doc_service.generate_daily_guardian_digest_html(today_str)
        
        # Assert
        self.assertIn("DAILY GUARDIAN OPERATIONS DIGEST", html)
        self.assertIn("दैनिक संरक्षक संचालन सारांश", html)

    def test_assign_branches_to_user(self):
        # Act
        self.admin_service.assign_branches_to_user("gdn_officer_test", ["1012", "1024"])
        
        # Assert - Verify user profile resolution has assigned branches
        user = self.admin_service.get_user("gdn_officer_test")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "gdn_officer_test")
        self.assertEqual(user.assigned_branches, ["1012", "1024"])


if __name__ == "__main__":
    unittest.main()
