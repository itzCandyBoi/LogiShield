import csv
import io
import unittest

from app import reconcile_uploads


class ReconciliationTests(unittest.TestCase):
    def test_reconcile_detects_quantity_discrepancy(self):
        invoice_content = """item,quantity,price
Widget A,100,12.50
Widget B,20,8.00
"""
        receipt_content = """item,quantity
Widget A,85
Widget B,20
"""

        invoice_file = io.BytesIO(invoice_content.encode("utf-8"))
        receipt_file = io.BytesIO(receipt_content.encode("utf-8"))

        details = reconcile_uploads(invoice_file, receipt_file)

        self.assertEqual(details["summary"]["total_discrepancies"], 1)
        self.assertEqual(details["discrepancies"][0]["item_name"], "Widget A")
        self.assertEqual(details["discrepancies"][0]["invoice_qty"], 100)
        self.assertEqual(details["discrepancies"][0]["receipt_qty"], 85)

    def test_reconcile_marks_small_deltas_as_low_risk(self):
        invoice_content = """item,quantity,price
Widget A,3,12.50
"""
        receipt_content = """item,quantity
Widget A,2
"""

        invoice_file = io.BytesIO(invoice_content.encode("utf-8"))
        receipt_file = io.BytesIO(receipt_content.encode("utf-8"))

        details = reconcile_uploads(invoice_file, receipt_file)

        self.assertEqual(details["discrepancies"][0]["severity"], "low")


if __name__ == "__main__":
    unittest.main()
