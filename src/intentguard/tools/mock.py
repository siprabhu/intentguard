class MockToolEnvironment:
    """In-memory tool environment for safe, reproducible experiments."""

    def __init__(self, resources: dict[str, object] | None = None):
        self.resources = dict(resources or {})
        self.trace: list[dict[str, object]] = []

    def execute(self, operation: str, resource: str) -> object:
        self.trace.append({"operation": operation, "resource": resource})
        if operation in {"search", "read", "get_balance", "get_transactions"}:
            return self.resources.get(resource)
        raise ValueError(f"Unsupported safe mock operation: {operation}")

