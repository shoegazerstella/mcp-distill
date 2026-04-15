"""
Core projection logic for filtering nested data structures.
"""

from __future__ import annotations
from typing import Any


class Projector:
    """
    Field projector for nested data structures.

    Supports:
    - Flat fields: "id", "name"
    - Nested fields with dot notation: "user.email", "config.settings.timeout"
    - Wildcards: "items.*" (all fields in items), "*.id" (id field in all objects)
    - Arrays: automatically maps projection over list items

    Example:
        projector = Projector(["id", "user.email", "items.*.name"])
        result = projector.apply(data)
    """

    def __init__(self, fields: list[str] | None = None):
        self.fields = fields or []

    def apply(self, data: Any) -> Any:
        """Apply field projection to data."""
        if not self.fields:
            return data
        return self._project(data, self.fields)

    def _project(self, data: Any, fields: list[str]) -> Any:
        """Recursively project fields from data."""
        if isinstance(data, list):
            return [self._project(item, fields) for item in data]

        if not isinstance(data, dict):
            return data

        result: dict[str, Any] = {}

        for field in fields:
            if "*" in field:
                # Wildcard: "items.*", "*.name", or "items.*.field"
                self._handle_wildcard(data, field, result)
            else:
                # Regular field: "id" or "user.email"
                value = self._get_nested(data, field)
                if value is not None:
                    self._set_nested(result, field, value)

        return result

    def _handle_wildcard(self, data: dict, pattern: str, result: dict) -> None:
        """Handle wildcard patterns like 'items.*' or '*.name'."""
        parts = pattern.split(".*")

        if pattern.startswith("*."):
            # "*.name" - get 'name' from all top-level dict values
            suffix = pattern[2:]
            for key, value in data.items():
                if isinstance(value, dict):
                    nested_val = self._get_nested(value, suffix)
                    if nested_val is not None:
                        if key not in result:
                            result[key] = {}
                        self._set_nested(result[key], suffix, nested_val)
        elif pattern.endswith(".*"):
            # "items.*" - get all fields from 'items'
            prefix = pattern[:-2]
            value = self._get_nested(data, prefix)
            if value is not None:
                self._set_nested(result, prefix, value)
        elif len(parts) == 2:
            # "items.*.name" - get 'name' from each item in list/dict
            prefix, suffix = parts[0], parts[1].lstrip(".")
            container = self._get_nested(data, prefix)
            if isinstance(container, list):
                projected = [
                    self._project(item, [suffix]) if isinstance(item, dict) else item
                    for item in container
                ]
                self._set_nested(result, prefix, projected)
            elif isinstance(container, dict):
                projected = {
                    k: self._project(v, [suffix]) if isinstance(v, dict) else v
                    for k, v in container.items()
                }
                self._set_nested(result, prefix, projected)

    def _get_nested(self, data: dict, path: str) -> Any:
        """Get a nested value using dot notation."""
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list):
                # Map over list items
                return [
                    self._get_nested(item, ".".join(keys[keys.index(key):]))
                    if isinstance(item, dict) else None
                    for item in current
                ]
            else:
                return None

        return current

    def _set_nested(self, data: dict, path: str, value: Any) -> None:
        """Set a nested value using dot notation."""
        keys = path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value


def project(data: Any, fields: list[str] | None = None) -> Any:
    """
    Convenience function for one-shot field projection.

    Args:
        data: The data to filter (dict, list of dicts, or any JSON-serializable)
        fields: List of field paths to include. Supports dot notation.

    Returns:
        Filtered data containing only requested fields.

    Example:
        >>> data = {"id": 1, "name": "Item", "huge_blob": "x" * 10000}
        >>> project(data, ["id", "name"])
        {"id": 1, "name": "Item"}
    """
    return Projector(fields).apply(data)
