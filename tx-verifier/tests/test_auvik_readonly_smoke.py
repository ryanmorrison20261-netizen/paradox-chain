import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from auvik_readonly_smoke import redacted_summary

class AuvikSmokeSummaryTests(unittest.TestCase):
    def test_counts_json_api_data_without_exposing_records(self):
        summary = redacted_summary({"data":[{"id":"private-1"},{"id":"private-2"}]})
        self.assertEqual(summary["record_count"], 2)
        self.assertEqual(len(summary["response_sha256"]), 64)
        self.assertNotIn("private", str(summary))

    def test_empty_result_is_zero(self):
        self.assertEqual(redacted_summary({"data":[]})["record_count"], 0)

    def test_unexpected_shape_is_not_dumped(self):
        summary = redacted_summary({"message":"sensitive text"})
        self.assertEqual(summary["record_count"], 0)
        self.assertNotIn("sensitive", str(summary))

if __name__ == "__main__":
    unittest.main()
