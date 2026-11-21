"""Keep precise user locations out of logs: uvicorn's access log prints the full URL with its query."""
import logging
import re

_LOCATION = re.compile(r"((?:from_|to_)?(?:lat|lng))=-?[0-9]+(?:\.[0-9]*)?", re.IGNORECASE)


def redact_location(text: str) -> str:
    return _LOCATION.sub(r"\1=REDACTED", text)


class RedactLocationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(redact_location(a) if isinstance(a, str) else a for a in record.args)
        if isinstance(record.msg, str):
            record.msg = redact_location(record.msg)
        return True
