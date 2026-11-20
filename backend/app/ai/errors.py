class AIError(Exception):
    """Base class. `code` is a stable machine-readable string that is safe to show to clients."""

    code = "ai_error"


class InvalidInput(AIError):
    code = "invalid_input"


class LLMNotConfigured(AIError):
    code = "llm_not_configured"


class LLMUnavailable(AIError):
    """Provider unreachable / overloaded even after retries."""

    code = "llm_unavailable"


class LLMRejected(AIError):
    """Provider refused the request (bad key, bad request). Retrying will not help."""

    code = "llm_rejected"


class LLMBadResponse(AIError):
    code = "llm_bad_response"


class TransportError(Exception):
    """Network-level failure inside an HTTP poster (timeout, DNS, reset). Always treated as transient."""


class ToolError(Exception):
    """A problem the MODEL should be told about (bad arguments, no location, not found...).
    `message` must never contain secrets or internal details."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
