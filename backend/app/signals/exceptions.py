"""Signal-specific exceptions."""


class SignalFetchError(Exception):
    """Raised when an external data source is unreachable or returns invalid data."""

    def __init__(self, source: str, detail: str) -> None:
        self.source = source
        self.detail = detail
        super().__init__(f"[{source}] {detail}")


class StaleDataError(SignalFetchError):
    """Raised when cached data exceeds its maximum acceptable age."""

    pass
