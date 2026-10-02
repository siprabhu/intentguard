"""IntentGuard research prototype."""

from .intent.contract import IntentContract
from .guard.authorization import Decision, ProposedAction, evaluate_action
from .guard.runtime import ExecutionResult, GuardedRuntime, ToolSpec

__all__ = ["Decision", "IntentContract", "ProposedAction", "evaluate_action",
           "ExecutionResult", "GuardedRuntime", "ToolSpec"]
