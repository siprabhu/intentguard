import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from intentguard import Decision, IntentContract, ProposedAction, evaluate_action


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.contract = IntentContract.from_dict({
            "objective": "Read invoice 123",
            "allowed_operations": ["search", "read"],
            "allowed_resources": ["invoice_123"],
            "prohibited_operations": ["send", "delete"],
            "max_action_count": 2,
        })

    def test_allows_in_scope_read(self):
        decision, _ = evaluate_action(self.contract, ProposedAction("read", "invoice_123"))
        self.assertEqual(decision, Decision.ALLOW)

    def test_blocks_prohibited_send(self):
        decision, _ = evaluate_action(
            self.contract,
            ProposedAction("send", "invoice_123", "external@example.com"),
        )
        self.assertEqual(decision, Decision.BLOCK)

    def test_blocks_resource_drift(self):
        decision, _ = evaluate_action(self.contract, ProposedAction("read", "payroll"))
        self.assertEqual(decision, Decision.BLOCK)

    def test_blocks_cumulative_violation(self):
        decision, _ = evaluate_action(
            self.contract,
            ProposedAction("read", "invoice_123"),
            prior_action_count=2,
        )
        self.assertEqual(decision, Decision.BLOCK)


if __name__ == "__main__":
    unittest.main()

