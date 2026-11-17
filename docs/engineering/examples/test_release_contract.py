import unittest

from release_contract import CheckResult, ReleaseBlocked, require_release


class ReleaseContractTests(unittest.TestCase):
    def test_complete_clean_evidence_passes(self):
        require_release(
            frozenset({"A", "B"}),
            [CheckResult("B", "PASS", 5, 0), CheckResult("A", "PASS", 10, 0)],
        )

    def test_bad_evidence_never_authorizes_release(self):
        clean = CheckResult("A", "PASS", 10, 0)
        cases = {
            "missing": [],
            "duplicate": [clean, clean],
            "unexpected": [CheckResult("B", "PASS", 10, 0)],
            "false_pass": [CheckResult("A", "PASS", 10, 1)],
            "error": [CheckResult("A", "ERROR", 10, 0)],
            "fail": [CheckResult("A", "FAIL", 10, 0)],
            "unknown": [CheckResult("A", "SKIPPED", 10, 0)],
            "empty": [CheckResult("A", "PASS", 0, 0)],
            "negative": [CheckResult("A", "PASS", 10, -1)],
            "impossible": [CheckResult("A", "PASS", 10, 11)],
            "bool_count": [CheckResult("A", "PASS", True, 0)],
            "bool_violations": [CheckResult("A", "PASS", 10, False)],
            "float": [CheckResult("A", "PASS", 10.0, 0)],
            "wrong_type": [None],
            "invalid_id": [CheckResult(None, "PASS", 10, 0)],
        }
        for name, results in cases.items():
            with self.subTest(name=name), self.assertRaises(ReleaseBlocked):
                require_release(frozenset({"A"}), results)

    def test_partial_coverage_blocks(self):
        with self.assertRaises(ReleaseBlocked):
            require_release(frozenset({"A", "B"}), [CheckResult("A", "PASS", 10, 0)])

    def test_empty_or_invalid_policy_blocks(self):
        for required in (frozenset(), frozenset({" "}), frozenset({None})):
            with self.subTest(required=required), self.assertRaises(ReleaseBlocked):
                require_release(required, [])


if __name__ == "__main__":
    unittest.main()
