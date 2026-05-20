from __future__ import annotations
import json
import os
from typing import List, Dict, Any
from src.core.paths import project_path

class ProductService:
    def __init__(self) -> None:
        self.data_path = project_path("data", "products.json")
        self._ensure_data()

    def _ensure_data(self) -> None:
        if not self.data_path.exists():
            default_data = {"products": []}
            os.makedirs(self.data_path.parent, exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=4, ensure_ascii=False)

    def list_products(self) -> List[Dict[str, Any]]:
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("products", [])
        except Exception:
            return []

    def add_product(self, product: Dict[str, Any]) -> None:
        products = self.list_products()
        products.append(product)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump({"products": products}, f, indent=4, ensure_ascii=False)

    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        all_p = self.list_products()
        return [p for p in all_p if p.get("category", "").lower() == category.lower()]
