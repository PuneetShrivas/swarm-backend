"""
Modular Swarm Agent Framework.
Provides dynamic filesystem-based agent packages with standardized assets:
config.json, prompt.md, tools.py, skills.json, and mcp.json.
"""

from app.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentProfile,
    ToolDefinition,
    SkillDefinition,
    MCPServerConfig,
)
from app.agents.registry import AgentRegistry, agent_registry

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "AgentProfile",
    "ToolDefinition",
    "SkillDefinition",
    "MCPServerConfig",
    "AgentRegistry",
    "agent_registry",
]
