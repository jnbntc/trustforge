"""Stable, sanitized errors shared by OCI parsing, transport and CLI."""


class OciError(Exception):
    """An expected failure whose message is safe to expose to the operator."""

    def __init__(self, code: str, message: str, exit_code: int = 5) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
