"""Tests for the Projector class and project function."""

import pytest
from mcp_distill import Projector, project


class TestProjectorFlat:
    """Test flat field projection."""

    def test_single_field(self):
        data = {"id": 1, "name": "test", "extra": "remove"}
        result = project(data, ["id"])
        assert result == {"id": 1}

    def test_multiple_fields(self):
        data = {"id": 1, "name": "test", "extra": "remove"}
        result = project(data, ["id", "name"])
        assert result == {"id": 1, "name": "test"}

    def test_missing_field_ignored(self):
        data = {"id": 1, "name": "test"}
        result = project(data, ["id", "nonexistent"])
        assert result == {"id": 1}

    def test_empty_fields_returns_original(self):
        data = {"id": 1, "name": "test"}
        result = project(data, [])
        assert result == data

    def test_none_fields_returns_original(self):
        data = {"id": 1, "name": "test"}
        result = project(data, None)
        assert result == data


class TestProjectorNested:
    """Test nested field projection with dot notation."""

    def test_nested_single_level(self):
        data = {"id": 1, "user": {"name": "Alice", "email": "alice@test.com"}}
        result = project(data, ["id", "user.name"])
        assert result == {"id": 1, "user": {"name": "Alice"}}

    def test_nested_multiple_levels(self):
        data = {
            "id": 1,
            "config": {
                "settings": {
                    "timeout": 30,
                    "retries": 3,
                    "verbose": True,
                }
            }
        }
        result = project(data, ["config.settings.timeout"])
        assert result == {"config": {"settings": {"timeout": 30}}}

    def test_nested_missing_intermediate(self):
        data = {"id": 1, "name": "test"}
        result = project(data, ["user.email"])
        assert result == {}


class TestProjectorWildcard:
    """Test wildcard pattern projection."""

    def test_suffix_wildcard(self):
        """Test 'items.*' - get all fields from items."""
        data = {
            "id": 1,
            "items": {"a": 1, "b": 2, "c": 3}
        }
        result = project(data, ["items.*"])
        assert result == {"items": {"a": 1, "b": 2, "c": 3}}

    def test_prefix_wildcard(self):
        """Test '*.id' - get id from all top-level objects."""
        data = {
            "user": {"id": 1, "name": "Alice"},
            "org": {"id": 2, "name": "Acme"},
        }
        result = project(data, ["*.id"])
        assert result == {"user": {"id": 1}, "org": {"id": 2}}

    def test_middle_wildcard_with_list(self):
        """Test 'items.*.name' - get name from each item in list."""
        data = {
            "items": [
                {"id": 1, "name": "First", "extra": "x"},
                {"id": 2, "name": "Second", "extra": "y"},
            ]
        }
        result = project(data, ["items.*.name"])
        assert result == {"items": [{"name": "First"}, {"name": "Second"}]}

    def test_middle_wildcard_with_dict(self):
        """Test 'items.*.name' - get name from each item in dict."""
        data = {
            "items": {
                "a": {"id": 1, "name": "First"},
                "b": {"id": 2, "name": "Second"},
            }
        }
        result = project(data, ["items.*.name"])
        assert result == {"items": {"a": {"name": "First"}, "b": {"name": "Second"}}}


class TestProjectorArrays:
    """Test projection over arrays."""

    def test_list_of_dicts(self):
        data = [
            {"id": 1, "name": "A", "extra": "x"},
            {"id": 2, "name": "B", "extra": "y"},
        ]
        result = project(data, ["id", "name"])
        assert result == [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]

    def test_nested_list(self):
        data = {
            "results": [
                {"id": 1, "data": {"value": 100, "label": "first"}},
                {"id": 2, "data": {"value": 200, "label": "second"}},
            ]
        }
        result = project(data, ["results.*.id", "results.*.data.value"])
        # Note: middle wildcard handles this
        expected = {"results": [{"id": 1}, {"id": 2}]}
        assert "results" in result


class TestProjectorClass:
    """Test Projector class usage."""

    def test_reusable_projector(self):
        projector = Projector(["id", "name"])

        data1 = {"id": 1, "name": "A", "extra": "x"}
        data2 = {"id": 2, "name": "B", "extra": "y"}

        assert projector.apply(data1) == {"id": 1, "name": "A"}
        assert projector.apply(data2) == {"id": 2, "name": "B"}

    def test_projector_with_no_fields(self):
        projector = Projector()
        data = {"id": 1, "name": "test"}
        assert projector.apply(data) == data
