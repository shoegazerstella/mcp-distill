"""
Decorator for MCP tools to enable field projection.
"""

from __future__ import annotations
import inspect
import json
from functools import wraps
from typing import Any, Callable, TypeVar

from inspect import signature, Parameter

from .projector import project

F = TypeVar("F", bound=Callable[..., Any])


def projectable(
    fn: F | None = None,
    *,
    fields: list[str] | None = None,
    field_param: str = "_fields",
    field_description: str | None = None,
) -> F | Callable[[F], F]:
    """
    Decorator that adds field projection capability to MCP tools.

    The decorated function will accept an additional `_fields` parameter.
    When provided, only the specified fields are returned.

    Args:
        fn: The function to decorate (when used without parentheses)
        fields: List of available field paths to advertise to the agent.
                These are included in the parameter description so the agent
                knows what fields it can request.
        field_param: Name of the projection parameter (default: "_fields")
        field_description: Custom description for the field parameter.
                          If not provided, auto-generates from `fields` list.

    Example:
        from fastmcp import FastMCP
        from mcp_distill import projectable

        mcp = FastMCP("my-server")

        @mcp.tool
        @projectable(fields=["id", "name", "metadata.created_by", "metadata.updated_at"])
        def get_resource(resource_id: str) -> dict:
            return {
                "id": resource_id,
                "name": "Example",
                "metadata": {"created_by": "admin", "updated_at": "2024-01-01", "huge": "x" * 5000},
                "content": "..." * 5000,
            }

        # Agent sees available fields in the tool schema and can request:
        # get_resource(resource_id="123", _fields=["id", "name"])
    """
    # Build description for the _fields parameter
    if field_description is not None:
        description = field_description
    elif fields:
        description = f"Fields to include in response. Available: {', '.join(fields)}. Omit for full response."
    else:
        description = "Fields to include in response. Supports dot notation (e.g., 'user.email'). Omit for full response."

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                requested = kwargs.pop(field_param, None)
                result = await func(*args, **kwargs)
                return _apply_projection(result, requested)

            wrapper = async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                requested = kwargs.pop(field_param, None)
                result = func(*args, **kwargs)
                return _apply_projection(result, requested)

            wrapper = sync_wrapper

        # Append available fields info to docstring (visible to agent)
        if fields:
            original_doc = func.__doc__ or ""
            fields_doc = f"\n\nProjectable fields: {', '.join(fields)}"
            wrapper.__doc__ = original_doc + fields_doc

        # Preserve original signature and add _fields parameter
        _extend_signature(wrapper, func, field_param, description)

        return wrapper  # type: ignore

    # Handle @projectable vs @projectable()
    if fn is not None:
        return decorator(fn)
    return decorator


def _apply_projection(result: Any, fields: list[str] | None) -> Any:
    """Apply field projection to a result."""
    if fields is None:
        return result

    # Handle common result types
    if isinstance(result, (dict, list)):
        return project(result, fields)

    # Try to handle string that might be JSON
    if isinstance(result, str):
        try:
            data = json.loads(result)
            return json.dumps(project(data, fields))
        except (json.JSONDecodeError, TypeError):
            pass

    return result


def _extend_signature(wrapper: Callable, original: Callable, param_name: str, description: str) -> None:
    """Add the _fields parameter to the function signature and annotations."""
    try:
        sig = signature(original)
        params = list(sig.parameters.values())

        # Add _fields parameter
        fields_param = Parameter(
            param_name,
            Parameter.KEYWORD_ONLY,
            default=None,
            annotation=list[str] | None,
        )
        params.append(fields_param)

        new_sig = sig.replace(parameters=params)
        wrapper.__signature__ = new_sig  # type: ignore

        # Update __annotations__ for compatibility with get_type_hints() / pydantic
        if not hasattr(wrapper, "__annotations__"):
            wrapper.__annotations__ = {}
        wrapper.__annotations__ = {
            **getattr(original, "__annotations__", {}),
            param_name: list[str] | None,
        }

        # Store description for schema generation
        wrapper.__projectable_field_param__ = param_name  # type: ignore
        wrapper.__projectable_field_description__ = description  # type: ignore
    except (ValueError, TypeError):
        pass
