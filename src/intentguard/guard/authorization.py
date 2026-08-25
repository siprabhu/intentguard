from dataclasses import dataclass
from enum import StrEnum

from intentguard.intent.contract import IntentContract


class Decision(StrEnum):
    ALLOW = "ALLOW"
    CONFIRM = "CONFIRM"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class ProposedAction:
    operation: str
    resource: str
    destination: str | None = None
    side_effect: str | None = None


def evaluate_action(
    contract: IntentContract,
    action: ProposedAction,
    *,
    prior_action_count: int = 0,
) -> tuple[Decision, str]:
    """Apply deterministic v1 authorization checks.

    Semantic alignment, provenance scoring, and trajectory policies will be
    added as independently testable modules after the deterministic baseline.
    """
    if action.operation in contract.prohibited_operations:
        return Decision.BLOCK, "operation is explicitly prohibited"
    if action.operation not in contract.allowed_operations:
        return Decision.BLOCK, "operation is outside the task scope"
    if action.resource not in contract.allowed_resources:
        return Decision.BLOCK, "resource is outside the task scope"
    if action.destination and action.destination not in contract.allowed_destinations:
        return Decision.BLOCK, "destination is outside the task scope"
    if contract.max_action_count is not None and prior_action_count >= contract.max_action_count:
        return Decision.BLOCK, "cumulative action limit would be exceeded"
    if action.side_effect in contract.confirmation_required:
        return Decision.CONFIRM, "explicit user confirmation is required"
    return Decision.ALLOW, "action satisfies deterministic contract checks"

