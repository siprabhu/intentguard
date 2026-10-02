"""Single-process execution boundary for trusted, bounded tool adapters.

The runtime/registry must be owned by the host, never exposed to untrusted
planner code. This is not isolation against a compromised Python process.
CONFIRM is suspended: authenticated approval is intentionally not implemented.
"""
from dataclasses import dataclass, replace
from collections import Counter
from threading import RLock
from typing import Callable

from .authorization import Decision, ProposedAction, evaluate_action
from ..intent.contract import IntentContract, identifier
from ..intent.trajectory import TrajectoryState


@dataclass(frozen=True)
class ToolSpec:
    handler: Callable[[ProposedAction], object]
    requires_destination: bool = False
    side_effect: str | None = None

    def __post_init__(self):
        if not callable(self.handler) or type(self.requires_destination) is not bool:
            raise ValueError("invalid tool handler or destination requirement")
        if self.side_effect is not None:
            identifier(self.side_effect, "tool side effect")


@dataclass(frozen=True)
class ExecutionResult:
    action: ProposedAction
    decision: Decision
    reason: str
    executed: bool
    charged_count: int
    output: object = None
    error: str | None = None


class GuardedRuntime:
    """Serialize authorization, budget charging, and bounded tool execution.

    Every admitted invocation consumes one unit, including failed invocations.
    BLOCK and CONFIRM consume none. Tools execute under the task lock; this
    correctness-first mock runtime is not a high-throughput network scheduler.
    """

    def __init__(self, contract: IntentContract, tools: dict[str, ToolSpec]):
        if not isinstance(contract, IntentContract):
            raise ValueError("a validated IntentContract is required")
        for operation, spec in tools.items():
            identifier(operation, "registered operation")
            if not isinstance(spec, ToolSpec):
                raise ValueError("registry entries must be ToolSpec objects")
        self._contract = contract
        self._tools = dict(tools)
        self._count = 0
        self._operation_counts = Counter()
        self._resource_counts = Counter()
        self._sequence_index = 0
        self._destinations = set()
        self._executing = False
        self._trace: list[ExecutionResult] = []
        self._lock = RLock()

    @property
    def charged_count(self) -> int:
        with self._lock:
            return self._count

    @property
    def trace(self) -> tuple[ExecutionResult, ...]:
        with self._lock:
            return tuple(self._trace)

    @property
    def trajectory_state(self) -> TrajectoryState:
        with self._lock:
            return TrajectoryState(tuple(self._operation_counts.items()),
                tuple(self._resource_counts.items()), self._sequence_index,
                frozenset(self._destinations))

    def execute(self, action: ProposedAction) -> ExecutionResult:
        if not isinstance(action, ProposedAction):
            raise ValueError("a validated ProposedAction is required")
        with self._lock:
            if self._executing:
                raise RuntimeError('tool handlers cannot reenter the same task runtime')
            spec = self._tools.get(action.operation)
            reason = None
            if spec is None:
                reason = "operation has no registered tool adapter"
            elif spec.requires_destination and action.destination is None:
                reason = "tool requires an explicit destination"
            elif not spec.requires_destination and action.destination is not None:
                reason = "tool does not accept a destination"
            elif action.side_effect is not None and action.side_effect != spec.side_effect:
                reason = "proposed side effect conflicts with trusted tool metadata"
            if reason:
                result = ExecutionResult(action, Decision.BLOCK, reason, False, self._count)
            else:
                normalized = replace(action, side_effect=spec.side_effect)
                decision, reason = evaluate_action(
                    self._contract, normalized, prior_action_count=self._count,
                    trajectory_state=self.trajectory_state,
                )
                output, error = None, None
                executed = decision == Decision.ALLOW
                if executed:
                    self._count += 1
                    self._operation_counts[normalized.operation] += 1
                    self._resource_counts[normalized.resource] += 1
                    if normalized.destination is not None:
                        self._destinations.add(normalized.destination)
                    self._executing = True
                    try:
                        output = spec.handler(normalized)
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {exc}"
                    else:
                        if self._contract.trajectory.operation_sequence:
                            self._sequence_index += 1
                    finally:
                        self._executing = False
                result = ExecutionResult(
                    normalized, decision, reason, executed, self._count, output, error,
                )
            self._trace.append(result)
            return result
