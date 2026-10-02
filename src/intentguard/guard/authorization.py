from dataclasses import dataclass
from enum import StrEnum

from intentguard.intent.contract import IntentContract, identifier
from intentguard.intent.trajectory import TrajectoryState


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

    def __post_init__(self):
        identifier(self.operation, "operation")
        identifier(self.resource, "resource")
        for name in ("destination", "side_effect"):
            value = getattr(self, name)
            if value is not None:
                identifier(value, name)

    @classmethod
    def from_dict(cls, value: dict) -> "ProposedAction":
        if not isinstance(value, dict):
            raise ValueError("action must be an object")
        if not {"operation", "resource"} <= value.keys():
            raise ValueError("action requires operation and resource")
        if value.keys() - cls.__dataclass_fields__.keys():
            raise ValueError("unknown action fields")
        return cls(**value)


def evaluate_action(
    contract: IntentContract,
    action: ProposedAction,
    *,
    prior_action_count: int = 0,
    trajectory_state: TrajectoryState | None = None,
) -> tuple[Decision, str]:
    """Apply deterministic v1 authorization checks.

    History is a trusted caller responsibility for direct predicate calls.
    GuardedRuntime owns it for executable workflows. Semantic alignment and
    provenance remain future work.
    """
    if type(prior_action_count) is not int or prior_action_count < 0:
        raise ValueError("prior_action_count must be a nonnegative integer")
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
    policy = contract.trajectory
    if policy.active:
        if not isinstance(trajectory_state, TrajectoryState):
            return Decision.BLOCK, "trusted trajectory state is required"
        operations = dict(trajectory_state.operation_counts)
        resources = dict(trajectory_state.resource_counts)
        if action.operation in dict(policy.operation_limits) and operations.get(action.operation, 0) >= dict(policy.operation_limits)[action.operation]:
            return Decision.BLOCK, "operation budget would be exceeded"
        if action.resource in dict(policy.resource_limits) and resources.get(action.resource, 0) >= dict(policy.resource_limits)[action.resource]:
            return Decision.BLOCK, "resource budget would be exceeded"
        if policy.operation_sequence:
            index = trajectory_state.sequence_index
            if index >= len(policy.operation_sequence) or action.operation != policy.operation_sequence[index]:
                return Decision.BLOCK, "operation is outside the authorized sequence"
        if (policy.max_distinct_destinations is not None and action.destination is not None
                and action.destination not in trajectory_state.destinations
                and len(trajectory_state.destinations) >= policy.max_distinct_destinations):
            return Decision.BLOCK, "distinct destination budget would be exceeded"
    if action.side_effect in contract.confirmation_required:
        return Decision.CONFIRM, "explicit user confirmation is required"
    return Decision.ALLOW, "action satisfies deterministic contract checks"
