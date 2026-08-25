from dataclasses import dataclass, field


@dataclass(frozen=True)
class IntentContract:
    objective: str
    allowed_operations: frozenset[str]
    allowed_resources: frozenset[str]
    allowed_destinations: frozenset[str] = field(default_factory=frozenset)
    prohibited_operations: frozenset[str] = field(default_factory=frozenset)
    confirmation_required: frozenset[str] = field(default_factory=frozenset)
    max_action_count: int | None = None

    @classmethod
    def from_dict(cls, value: dict) -> "IntentContract":
        return cls(
            objective=value["objective"],
            allowed_operations=frozenset(value.get("allowed_operations", [])),
            allowed_resources=frozenset(value.get("allowed_resources", [])),
            allowed_destinations=frozenset(value.get("allowed_destinations", [])),
            prohibited_operations=frozenset(value.get("prohibited_operations", [])),
            confirmation_required=frozenset(value.get("confirmation_required", [])),
            max_action_count=value.get("max_action_count"),
        )

