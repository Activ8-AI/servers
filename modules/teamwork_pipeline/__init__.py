"""
Teamwork pipeline package.

This module exposes the primary `TeamworkPipeline` orchestration class together
with the `ExecutionIntent` schema helper and the base exception type.  The
pipeline bridges Reflex outputs (execution intents) into actionable Teamwork
tasks, including optional sprint creation, notifications, and Custodian Hub
logging.
"""

from .pipeline import (
    ExecutionIntent,
    TeamworkPipeline,
    TeamworkPipelineError,
)

__all__ = [
    "ExecutionIntent",
    "TeamworkPipeline",
    "TeamworkPipelineError",
]
