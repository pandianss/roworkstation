import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from src.application.use_cases.mis.service import MISAnalyticsService
from src.domain.schemas.mis import MISFilter


class MisUseCaseTests(unittest.TestCase):
    def test_build_snapshot_computes_kpis_from_processed_frame(self):
        frame = pd.DataFrame(
            [
                {"DATE": pd.Timestamp("2026-04-01"), "SOL": 3933, "Total Advances": 100.0, "Total Deposits": 200.0, "NPA": 5.0, "CD Ratio": 50.0},
                {"DATE": pd.Timestamp("2026-04-01"), "SOL": 1001, "Total Advances": 80.0, "Total Deposits": 160.0, "NPA": 4.0, "CD Ratio": 50.0},
                {"DATE": pd.Timestamp("2026-03-01"), "SOL": 3933, "Total Advances": 90.0, "Total Deposits": 180.0, "NPA": 3.0, "CD Ratio": 50.0},
            ]
        )
        service = object.__new__(MISAnalyticsService)
        service.settings = SimpleNamespace(region_code="3933")
        with patch.object(service, "load_frame", return_value=frame):
            snapshot = service.build_snapshot(MISFilter(selected_date=date(2026, 4, 1), sols=[1001]))
        self.assertEqual(snapshot.kpis["Total Advances"], 80.0)
        self.assertEqual(snapshot.kpis["Total Deposits"], 160.0)
        self.assertEqual(snapshot.selected_date, date(2026, 4, 1))
