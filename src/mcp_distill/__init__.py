"""
mcp-distill: Field projection layer for MCP tools.

Reduce LLM context window usage by letting agents request only the fields they need.
"""

from .projector import Projector, project
from .decorator import projectable

__all__ = ["Projector", "project", "projectable"]
__version__ = "0.1.0"
