from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.logging.audit import AuditLogger
from src.core.paths import project_path


class OperationService:
    def __init__(self, accounts_path: Path | None = None, operations_path: Path | None = None) -> None:
        self.accounts_path = accounts_path or project_path("data", "accounts.json")
        self.operations_path = operations_path or project_path("data", "operations.json")
        self.audit_logger = AuditLogger()
        self.accounts_path.parent.mkdir(parents=True, exist_ok=True)
        self.operations_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.accounts_path.exists():
            self.accounts_path.write_text("[]", encoding="utf-8")
        if not self.operations_path.exists():
            self.operations_path.write_text("[]", encoding="utf-8")

    def process_operation(self, payload: dict[str, Any], user: str) -> dict[str, Any]:
        accounts = self._read_json(self.accounts_path)
        source = self._find_account(accounts, payload.get("account"))
        if not source:
            return {"success": False, "message": "Source account not found."}

        operation_type = payload.get("type", "")
        if operation_type == "Transfer":
            return self._transfer(accounts, source, payload, user)
        if operation_type == "Closure":
            return self._close_account(accounts, source, payload, user)
        if operation_type == "Update":
            return self._update_account(accounts, source, payload, user)
        return {"success": False, "message": f"Unsupported operation type: {operation_type}"}

    def _transfer(self, accounts: list[dict], source: dict, payload: dict[str, Any], user: str) -> dict[str, Any]:
        amount = float(payload.get("amount") or 0)
        destination = self._find_account(accounts, payload.get("destination_account"))
        if amount <= 0:
            return {"success": False, "message": "Transfer amount must be greater than zero."}
        if not destination:
            return {"success": False, "message": "Destination account not found."}
        if float(source.get("balance", 0)) < amount:
            return {"success": False, "message": "Insufficient balance."}

        source["balance"] = float(source.get("balance", 0)) - amount
        destination["balance"] = float(destination.get("balance", 0)) + amount
        self._write_json(self.accounts_path, accounts)
        self._record_operation(payload, user, "Transfer completed")
        return {"success": True, "message": "Transfer completed."}

    def _close_account(self, accounts: list[dict], source: dict, payload: dict[str, Any], user: str) -> dict[str, Any]:
        if float(source.get("balance", 0)) != 0:
            return {"success": False, "message": "Account balance must be zero before closure."}
        source["status"] = "CLOSED"
        source["remarks"] = payload.get("remarks", source.get("remarks", ""))
        self._write_json(self.accounts_path, accounts)
        self._record_operation(payload, user, "Account closed")
        return {"success": True, "message": "Account closed."}

    def _update_account(self, accounts: list[dict], source: dict, payload: dict[str, Any], user: str) -> dict[str, Any]:
        field = payload.get("update_field")
        if not field:
            return {"success": False, "message": "Update field is required."}
        source[field] = payload.get("update_value", "")
        self._write_json(self.accounts_path, accounts)
        self._record_operation(payload, user, f"Updated {field}")
        return {"success": True, "message": "Account updated."}

    def _record_operation(self, payload: dict[str, Any], user: str, message: str) -> None:
        operations = self._read_json(self.operations_path)
        operations.append({"timestamp": datetime.now().isoformat(), "user": user, "message": message, "payload": payload})
        self._write_json(self.operations_path, operations)
        self.audit_logger.log(user, message)

    @staticmethod
    def _find_account(accounts: list[dict], account_number: str | None) -> dict | None:
        return next((account for account in accounts if account.get("account_number") == account_number), None)

    @staticmethod
    def _read_json(path: Path) -> list[dict]:
        return json.loads(path.read_text(encoding="utf-8") or "[]")

    @staticmethod
    def _write_json(path: Path, data: list[dict]) -> None:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
