import unittest
from src.core.utils.number_utils import format_indian_number

class TestNumberUtils(unittest.TestCase):
    def test_indian_formatting(self):
        self.assertEqual(format_indian_number(1000), "1,000.00")
        self.assertEqual(format_indian_number(10000), "10,000.00")
        self.assertEqual(format_indian_number(100000), "1,00,000.00")
        self.assertEqual(format_indian_number(1000000), "10,00,000.00")
        self.assertEqual(format_indian_number(1234567.89), "12,34,567.89")
        self.assertEqual(format_indian_number(10000000), "1,00,00,000.00")
        self.assertEqual(format_indian_number(123456789.123), "12,34,56,789.12")
        
    def test_negative_numbers(self):
        self.assertEqual(format_indian_number(-100000), "-1,00,000.00")
        
    def test_symbols(self):
        self.assertEqual(format_indian_number(100000, include_symbol=True), "₹ 1,00,000.00")
        
    def test_edge_cases(self):
        self.assertEqual(format_indian_number(0), "0.00")
        self.assertEqual(format_indian_number(None), "0.00")
        self.assertEqual(format_indian_number(""), "0.00")
        self.assertEqual(format_indian_number("1,00,000"), "1,00,000.00")

if __name__ == '__main__':
    unittest.main()
