import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

from src.application.services.operation_service import OperationService
from src.core.paths import project_path


class OperationServiceTests(unittest.TestCase):
    def setUp(self):
        temp_path = project_path("data", "test_runtime", f"ro_ws_ops_{uuid4().hex}")
        temp_path.mkdir(parents=True, exist_ok=True)
        self.temp_path = temp_path
        self.accounts_file = temp_path / "accounts.json"
        self.operations_file = temp_path / "operations.json"
        self.accounts_file.write_text(
            json.dumps(
                [
                    {"account_number": "A1", "branch": "RO001", "holder_name": "Source", "balance": 1000.0, "status": "ACTIVE", "remarks": ""},
                    {"account_number": "A2", "branch": "RO002", "holder_name": "Destination", "balance": 250.0, "status": "ACTIVE", "remarks": ""},
                    {"account_number": "A3", "branch": "RO001", "holder_name": "Closure", "balance": 0.0, "status": "ACTIVE", "remarks": ""},
                ]
            ),
            encoding="utf-8",
        )
        self.operations_file.write_text("[]", encoding="utf-8")
        self.service = OperationService(accounts_path=self.accounts_file, operations_path=self.operations_file)
        self.service.audit_logger = MagicMock()

    def tearDown(self):
        return None

    def test_transfer_updates_source_and_destination_balances(self):
        result = self.service.process_operation(
            {
                "branch": "RO001",
                "account": "A1",
                "amount": 300.0,
                "type": "Transfer",
                "remarks": "Move funds",
                "destination_account": "A2",
                "update_field": "",
                "update_value": "",
            },
            user="tester",
        )
        self.assertTrue(result["success"])
        accounts = json.loads(self.accounts_file.read_text(encoding="utf-8"))
        source = next(account for account in accounts if account["account_number"] == "A1")
        destination = next(account for account in accounts if account["account_number"] == "A2")
        self.assertEqual(source["balance"], 700.0)
        self.assertEqual(destination["balance"], 550.0)

    def test_closure_requires_zero_balance(self):
        result = self.service.process_operation(
            {
                "branch": "RO001",
                "account": "A1",
                "amount": 0.0,
                "type": "Closure",
                "remarks": "Close this account",
                "destination_account": "",
                "update_field": "",
                "update_value": "",
            },
            user="tester",
        )
        self.assertFalse(result["success"])
        self.assertIn("balance must be zero", result["message"])
