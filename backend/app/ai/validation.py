"""Strict argument validation for tool calls (a small JSON-Schema subset).
Strict on purpose: unknown fields are rejected, strings are never coerced into numbers."""
import math
from typing import Any

from .errors import ToolError


def _bad(name: str, why: str) -> ToolError:
    return ToolError("invalid_arguments", f"'{name}' {why}")


def _check(name: str, value: Any, spec: dict[str, Any]) -> Any:
    t = spec.get("type")
    if t == "string":
        if not isinstance(value, str):
            raise _bad(name, "must be a string")
        value = value.strip()
        if "minLength" in spec and len(value) < spec["minLength"]:
            raise _bad(name, f"must have at least {spec['minLength']} characters")
        if "maxLength" in spec and len(value) > spec["maxLength"]:
            raise _bad(name, f"must have at most {spec['maxLength']} characters")
        if "enum" in spec and value not in spec["enum"]:
            raise _bad(name, f"must be one of {spec['enum']}")
        return value
    if t in ("number", "integer"):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise _bad(name, f"must be a {t}")
        if t == "integer" and isinstance(value, float):
            if not value.is_integer():
                raise _bad(name, "must be an integer")
            value = int(value)
        if isinstance(value, float) and not math.isfinite(value):
            raise _bad(name, "must be a finite number")
        if "minimum" in spec and value < spec["minimum"]:
            raise _bad(name, f"must be >= {spec['minimum']}")
        if "maximum" in spec and value > spec["maximum"]:
            raise _bad(name, f"must be <= {spec['maximum']}")
        return value
    if t == "boolean":
        if not isinstance(value, bool):
            raise _bad(name, "must be a boolean")
        return value
    if t == "array":
        if not isinstance(value, list):
            raise _bad(name, "must be a list")
        if "maxItems" in spec and len(value) > spec["maxItems"]:
            raise _bad(name, f"must have at most {spec['maxItems']} items")
        if "minItems" in spec and len(value) < spec["minItems"]:
            raise _bad(name, f"must have at least {spec['minItems']} items")
        item_spec = spec.get("items", {})
        return [_check(f"{name}[]", v, item_spec) for v in value]
    raise _bad(name, "has an unsupported schema type")  # programming error, but never crash


def validate_args(args: Any, schema: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ToolError("invalid_arguments", "arguments must be a JSON object")
    props: dict[str, Any] = schema.get("properties", {})
    unknown = sorted(set(args) - set(props))
    if unknown:
        raise ToolError("invalid_arguments", f"unknown fields: {unknown}")
    for name in schema.get("required", []):
        if args.get(name) is None:
            raise ToolError("invalid_arguments", f"'{name}' is required")
    out: dict[str, Any] = {}
    for name, spec in props.items():
        if args.get(name) is not None:
            out[name] = _check(name, args[name], spec)
        elif "default" in spec:
            out[name] = spec["default"]
    return out
