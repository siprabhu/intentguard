from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from intentguard import IntentContract, ProposedAction, evaluate_action

contract = IntentContract.from_dict({
    "objective": "Find invoice 123 and report its amount",
    "allowed_operations": ["search", "read"],
    "allowed_resources": ["invoice_123"],
    "prohibited_operations": ["send", "delete", "modify"],
})

for action in (
    ProposedAction("read", "invoice_123"),
    ProposedAction("send", "invoice_123", "external@example.com"),
):
    decision, reason = evaluate_action(contract, action)
    print(f"{action.operation}: {decision} - {reason}")

