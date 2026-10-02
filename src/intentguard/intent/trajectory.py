"""Immutable, explicit trajectory constraints; no learned or inferred policy."""
from dataclasses import dataclass, field


def limits(value, name):
    if isinstance(value, dict):
        value = tuple(value.items())
    if not isinstance(value, (tuple, list)):
        raise ValueError(f'{name} must be a mapping or pairs')
    result = []
    for pair in value:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError(f'{name} requires identifier/count pairs')
        key, count = pair
        if not isinstance(key, str) or not key or key.strip() != key:
            raise ValueError(f'invalid {name} identifier')
        if type(count) is not int or count < 0:
            raise ValueError(f'{name} counts must be nonnegative integers')
        result.append((key, count))
    if len({key for key, _ in result}) != len(result):
        raise ValueError(f'{name} contains duplicate keys')
    return tuple(sorted(result))


@dataclass(frozen=True)
class TrajectoryPolicy:
    operation_limits: tuple[tuple[str, int], ...] = ()
    resource_limits: tuple[tuple[str, int], ...] = ()
    operation_sequence: tuple[str, ...] = ()
    max_distinct_destinations: int | None = None

    def __post_init__(self):
        for name in ('operation_limits', 'resource_limits'):
            object.__setattr__(self, name, limits(getattr(self, name), name))
        sequence = self.operation_sequence
        if not isinstance(sequence, (list, tuple)):
            raise ValueError('operation_sequence must be an ordered list')
        for op in sequence:
            if not isinstance(op, str) or not op or op.strip() != op:
                raise ValueError('invalid sequence operation')
        object.__setattr__(self, 'operation_sequence', tuple(sequence))
        if self.max_distinct_destinations is not None and (
            type(self.max_distinct_destinations) is not int or self.max_distinct_destinations < 1
        ):
            raise ValueError('max_distinct_destinations must be a positive integer or None')

    @property
    def active(self):
        return bool(self.operation_limits or self.resource_limits or
                    self.operation_sequence or self.max_distinct_destinations is not None)

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or value.keys() - cls.__dataclass_fields__.keys():
            raise ValueError('invalid trajectory policy fields')
        return cls(**value)


@dataclass(frozen=True)
class TrajectoryState:
    """Snapshot supplied by the trusted runtime; not planner authority."""
    operation_counts: tuple[tuple[str, int], ...] = ()
    resource_counts: tuple[tuple[str, int], ...] = ()
    sequence_index: int = 0
    destinations: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self):
        for name in ('operation_counts', 'resource_counts'):
            object.__setattr__(self, name, limits(getattr(self, name), name))
        if type(self.sequence_index) is not int or self.sequence_index < 0:
            raise ValueError('sequence_index must be nonnegative')
        if not isinstance(self.destinations, (list, tuple, set, frozenset)):
            raise ValueError('destinations must be a collection')
        if any(not isinstance(d, str) or not d or d.strip() != d for d in self.destinations):
            raise ValueError('invalid historical destination')
        object.__setattr__(self, 'destinations', frozenset(self.destinations))
