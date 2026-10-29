"""
Model Context Protocol (MCP) Manager and Server Registry.
Provides runtime execution and native in-process tool dispatchers for MCP servers
configured across Swarm agents.
"""

from app.mcp.manager import MCPManager, mcp_manager

__all__ = ["MCPManager", "mcp_manager"]
