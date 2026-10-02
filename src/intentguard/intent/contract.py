from dataclasses import dataclass, field


def identifier(value: object, name: str) -> None:
    """Reject ambiguous identifiers; normalization belongs to the trusted adapter."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{name} must be a nonempty, trimmed string")


@dataclass(frozen=True)
class IntentContract:
    objective: str
    allowed_operations: frozenset[str]
    allowed_resources: frozenset[str]
    allowed_destinations: frozenset[str] = field(default_factory=frozenset)
    prohibited_operations: frozenset[str] = field(default_factory=frozenset)
    confirmation_required: frozenset[str] = field(default_factory=frozenset)
    max_action_count: int | None = None

    def __post_init__(self):
        identifier(self.objective, "objective")
        for name in (
            "allowed_operations", "allowed_resources", "allowed_destinations",
            "prohibited_operations", "confirmation_required",
        ):
            values = getattr(self, name)
            if not isinstance(values, (list, tuple, set, frozenset)):
                raise ValueError(f"{name} must be a collection of identifiers")
            for value in values:
                identifier(value, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicate identifiers")
            object.__setattr__(self, name, frozenset(values))
        if self.max_action_count is not None and (
            type(self.max_action_count) is not int or self.max_action_count < 1
        ):
            raise ValueError("max_action_count must be a positive integer or None")

    @classmethod
    def from_dict(cls, value: dict) -> "IntentContract":
        if not isinstance(value, dict):
            raise ValueError("contract must be an object")
        required = {"objective", "allowed_operations", "allowed_resources"}
        if not required <= value.keys():
            raise ValueError(f"missing contract fields: {sorted(required - value.keys())}")
        unknown = value.keys() - cls.__dataclass_fields__.keys()
        if unknown:
            raise ValueError(f"unknown contract fields: {sorted(unknown)}")
        return cls(**value)
