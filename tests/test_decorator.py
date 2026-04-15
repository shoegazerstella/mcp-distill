"""Tests for the @projectable decorator."""

import pytest
from mcp_distill import projectable


class TestProjectableSync:
    """Test @projectable with synchronous functions."""

    def test_basic_projection(self):
        @projectable
        def get_item(item_id: str) -> dict:
            return {
                "id": item_id,
                "name": "Test Item",
                "description": "A" * 1000,
                "metadata": {"created": "2024-01-01", "updated": "2024-01-02"},
            }

        result = get_item("123", _fields=["id", "name"])
        assert result == {"id": "123", "name": "Test Item"}

    def test_nested_projection(self):
        @projectable
        def get_item(item_id: str) -> dict:
            return {
                "id": item_id,
                "name": "Test",
                "metadata": {"created": "2024-01-01", "author": "admin"},
            }

        result = get_item("123", _fields=["id", "metadata.author"])
        assert result == {"id": "123", "metadata": {"author": "admin"}}

    def test_no_fields_returns_full(self):
        @projectable
        def get_item() -> dict:
            return {"id": 1, "name": "Test", "extra": "data"}

        result = get_item()
        assert result == {"id": 1, "name": "Test", "extra": "data"}

    def test_empty_fields_returns_full(self):
        """Empty fields list returns full result (no projection applied)."""
        @projectable
        def get_item() -> dict:
            return {"id": 1, "name": "Test"}

        result = get_item(_fields=[])
        assert result == {"id": 1, "name": "Test"}

    def test_list_result(self):
        @projectable
        def list_items() -> list:
            return [
                {"id": 1, "name": "A", "extra": "x"},
                {"id": 2, "name": "B", "extra": "y"},
            ]

        result = list_items(_fields=["id", "name"])
        assert result == [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]


class TestProjectableAsync:
    """Test @projectable with async functions."""

    @pytest.mark.asyncio
    async def test_async_projection(self):
        @projectable
        async def get_item(item_id: str) -> dict:
            return {
                "id": item_id,
                "name": "Test",
                "huge_field": "x" * 10000,
            }

        result = await get_item("123", _fields=["id", "name"])
        assert result == {"id": "123", "name": "Test"}

    @pytest.mark.asyncio
    async def test_async_no_fields(self):
        @projectable
        async def get_item() -> dict:
            return {"id": 1, "name": "Test"}

        result = await get_item()
        assert result == {"id": 1, "name": "Test"}


class TestProjectableCustomParam:
    """Test @projectable with custom parameter name."""

    def test_custom_param_name(self):
        @projectable(field_param="_select")
        def get_item() -> dict:
            return {"id": 1, "name": "Test", "extra": "data"}

        result = get_item(_select=["id"])
        assert result == {"id": 1}

    def test_with_parentheses_no_args(self):
        @projectable()
        def get_item() -> dict:
            return {"id": 1, "name": "Test"}

        result = get_item(_fields=["id"])
        assert result == {"id": 1}


class TestProjectableEdgeCases:
    """Test edge cases for @projectable."""

    def test_non_dict_result(self):
        @projectable
        def get_value() -> str:
            return "hello"

        result = get_value(_fields=["anything"])
        assert result == "hello"

    def test_json_string_result(self):
        import json

        @projectable
        def get_json() -> str:
            return json.dumps({"id": 1, "name": "Test", "extra": "data"})

        result = get_json(_fields=["id", "name"])
        assert json.loads(result) == {"id": 1, "name": "Test"}

    def test_preserves_function_metadata(self):
        @projectable
        def documented_function() -> dict:
            """This is the docstring."""
            return {}

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is the docstring."
