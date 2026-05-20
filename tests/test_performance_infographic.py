import unittest
from src.application.services.graphic_service import GraphicService

class PerformanceInfographicTests(unittest.TestCase):
    def test_generate_performance_infographic_returns_valid_png_bytes(self):
        service = GraphicService()
        
        top_branches = [
            {"name": "DINDIGUL MAIN", "value": "₹ 154.20 Cr"},
            {"name": "PALANI", "value": "₹ 112.10 Cr"},
            {"name": "NATHAM", "value": "₹ 98.45 Cr"}
        ]
        
        bottom_branches = [
            {"name": "ODDANCHATRAM", "value": "₹ -12.40 Cr", "rank": 40},
            {"name": "VEDASANDUR", "value": "₹ -8.10 Cr", "rank": 39},
            {"name": "BATLAGUNDU", "value": "₹ -5.20 Cr", "rank": 38}
        ]
        
        result = service.generate_performance_infographic(
            title="Dindigul Region",
            subtitle="Performance League",
            metric_label="Total Advances (ADV)",
            basis_label="FY Growth (₹ Cr)",
            date_str="April 2026",
            top_branches=top_branches,
            bottom_branches=bottom_branches
        )
        
        # Verify the result starts with standard PNG magic header
        self.assertTrue(result.startswith(b"\x89PNG"))

if __name__ == "__main__":
    unittest.main()
