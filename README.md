# mcp-distill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Field projection layer for MCP tools. Reduce LLM context window usage by letting agents request only the fields they need.

## The Problem

MCP tools often return large JSON responses. When an agent only needs a few fields, the full response wastes precious context window tokens.

```
Without mcp-distill (1,157 tokens):
{"id": "123", "name": "Item", "description": "...(2000 chars)...", "metadata": {...}, "content": "...(10000 chars)..."}

With mcp-distill (23 tokens):
{"id": "123", "name": "Item"}
```

## Installation

```bash
pip install git+https://github.com/shoegazerstella/mcp-distill.git
```

Or with uv:

```bash
uv add git+https://github.com/shoegazerstella/mcp-distill.git
```

## Quick Start

```python
from fastmcp import FastMCP
from mcp_distill import projectable

mcp = FastMCP("my-server")

@mcp.tool
@projectable(fields=["id", "name", "metadata.created_by"])
def get_resource(resource_id: str) -> dict:
    """Fetch a resource by ID."""
    return {
        "id": resource_id,
        "name": "Example Resource",
        "description": "A" * 2000,      # Large field - not advertised
        "metadata": {
            "created_by": "admin",
            "huge_audit_log": [...],    # Large field - not advertised
        },
        "content": "B" * 10000,         # Large field - not advertised
    }
```

## How It Works

### 1. You advertise available fields

The `fields` parameter in `@projectable()` tells the agent what fields it can request:

```python
@projectable(fields=["id", "name", "metadata.created_by"])
```

### 2. The agent sees them in the tool description

```
Tool: get_resource
Description: Fetch a resource by ID.

Projectable fields: id, name, metadata.created_by

Parameters:
  - resource_id: string (required)
  - _fields: array of strings (optional)
```

### 3. The agent requests only what it needs

```python
# Agent needs just the ID and name
get_resource(resource_id="123", _fields=["id", "name"])
# Returns: {"id": "123", "name": "Example Resource"}

# Agent needs everything (omits _fields)
get_resource(resource_id="123")
# Returns: full response
```

## Field Syntax

| Pattern | Description | Example |
|---------|-------------|---------|
| `field` | Top-level field | `"id"`, `"name"` |
| `a.b.c` | Nested field (dot notation) | `"metadata.created_by"` |
| `items.*` | All fields in object | `"config.*"` |
| `*.field` | Field from all top-level objects | `"*.id"` |
| `items.*.field` | Field from each item in array/dict | `"results.*.name"` |

## Usage Without FastMCP

### Standalone function

```python
from mcp_distill import project

data = {
    "id": 1,
    "name": "Item",
    "nested": {"a": 1, "b": 2},
    "large_blob": "x" * 10000,
}

result = project(data, ["id", "name", "nested.a"])
# {"id": 1, "name": "Item", "nested": {"a": 1}}
```

### Reusable projector

```python
from mcp_distill import Projector

slim = Projector(["id", "name", "status"])

for item in large_dataset:
    yield slim.apply(item)
```

### Decorator on any function

```python
from mcp_distill import projectable

@projectable(fields=["id", "name", "email"])
def fetch_user(user_id: str) -> dict:
    return db.get_user(user_id)

# With projection
fetch_user("123", _fields=["id", "name"])

# Without projection (full response)
fetch_user("123")
```

## API Reference

### `@projectable`

```python
@projectable(
    fields=["id", "name", ...],  # Available fields (shown to agent)
    field_param="_fields",       # Parameter name (default: "_fields")
    field_description="...",     # Custom parameter description
)
```

### `project(data, fields)`

```python
project(data: Any, fields: list[str] | None) -> Any
```

### `Projector`

```python
projector = Projector(["id", "name"])
result = projector.apply(data)
```

## Development

```bash
git clone https://github.com/shoegazerstella/mcp-distill
cd mcp-distill
uv sync --dev
uv run pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
