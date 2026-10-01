from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from intentguard import GuardedRuntime, IntentContract, ProposedAction, ToolSpec
from intentguard.tools.mock import MockToolEnvironment

contract = IntentContract.from_dict({
    "objective": "Find invoice 123 and report its amount",
    "allowed_operations": ["search", "read"],
    "allowed_resources": ["invoice_123"],
    "prohibited_operations": ["send", "delete", "modify"],
})

environment = MockToolEnvironment({"invoice_123": {"amount": 100}})
runtime = GuardedRuntime(contract, {
    "read": ToolSpec(lambda action: environment.execute(action.operation, action.resource)),
    # Synthetic only: the prohibited operation must never reach this handler.
    "send": ToolSpec(lambda action: {"mock_sent": True}, True, "external_communication"),
})

for action in (
    ProposedAction("read", "invoice_123"),
    ProposedAction("send", "invoice_123", "external@example.com"),
):
    result = runtime.execute(action)
    print(f"{action.operation}: {result.decision} - {result.reason}; executed={result.executed}")

print(f"Charged actions: {runtime.charged_count}; read-tool trace: {environment.trace}")
