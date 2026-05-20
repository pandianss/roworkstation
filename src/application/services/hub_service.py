from __future__ import annotations

from typing import Any
from src.core.paths import project_path
from src.infrastructure.persistence.json_repo import JsonRepository


class KnowledgeHubService:
    def __init__(self) -> None:
        self.circular_repo = JsonRepository(project_path("data", "circulars.json"), {"circulars": []})
        self.product_repo = JsonRepository(project_path("data", "products.json"), {"products": []})
        self.survey_repo = JsonRepository(project_path("data", "surveys.json"), {"surveys": []})

    # Circulars
    def list_circulars(self, category: str | None = None) -> list[dict[str, Any]]:
        circulars = self.circular_repo.read().get("circulars", [])
        return [c for c in circulars if c.get("category") == category] if category else circulars

    def add_circular(self, entry: dict[str, Any]) -> None:
        data = self.circular_repo.read()
        data["circulars"].append(entry)
        self.circular_repo.write(data)

    # Products
    def list_products(self) -> list[dict[str, Any]]:
        return self.product_repo.read().get("products", [])

    def add_product(self, entry: dict[str, Any]) -> None:
        data = self.product_repo.read()
        data["products"].append(entry)
        self.product_repo.write(data)

    # Surveys
    def list_surveys(self) -> list[dict[str, Any]]:
        return self.survey_repo.read().get("surveys", [])

    def add_survey(self, entry: dict[str, Any]) -> None:
        data = self.survey_repo.read()
        data["surveys"].append(entry)
        self.survey_repo.write(data)
