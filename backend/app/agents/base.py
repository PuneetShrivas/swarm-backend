import os
import json
import importlib.util
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str = Field(..., description="Unique tool name")
    description: str = Field(..., description="Clear explanation of the tool's purpose")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema of parameters")
    handler_name: Optional[str] = Field(None, description="Name of the python callable in tools.py")


class SkillDefinition(BaseModel):
    id: str = Field(..., description="Unique skill identifier")
    name: str = Field(..., description="Human-readable skill name")
    description: str = Field(..., description="Description of the capability")
    triggers: List[str] = Field(default_factory=list, description="Keywords or phrases that trigger this skill")


class MCPServerConfig(BaseModel):
    name: str = Field(..., description="MCP server identifier")
    transport: str = Field(default="stdio", description="'stdio' or 'sse'")
    command: Optional[str] = Field(None, description="Command to execute for stdio transport (e.g. 'npx')")
    args: Optional[List[str]] = Field(default_factory=list, description="CLI arguments for stdio command")
    url: Optional[str] = Field(None, description="URL endpoint for SSE transport")
    tools: List[str] = Field(default_factory=list, description="Exposed MCP tools list")
    env: Optional[Dict[str, str]] = Field(default_factory=dict, description="Custom environment variables")


class AgentConfig(BaseModel):
    id: str = Field(..., description="Unique agent identifier (e.g. 'coder', 'orchestrator')")
    name: str = Field(..., description="Display name for the agent")
    role: str = Field(..., description="Primary specialty and responsibility")
    status: str = Field(default="active", description="Operational state ('active', 'busy', 'idle')")
    model: str = Field(default="gemini-3.8-flash", description="Underlying Gemini model")
    temperature: float = Field(default=0.3, description="Sampling temperature")
    is_orchestrator: bool = Field(default=False, description="Whether this agent acts as the swarm orchestrator")
    icon: Optional[str] = Field(None, description="Lucide icon identifier for UI rendering")
    description: Optional[str] = Field(None, description="Extended summary of agent capabilities")


class AgentProfile(BaseModel):
    id: str
    name: str
    role: str
    status: str = "active"
    system_prompt: Optional[str] = None
    model: str = "gemini-3.8-flash"
    temperature: float = 0.3
    is_orchestrator: bool = False
    icon: Optional[str] = None
    description: Optional[str] = None
    tools: List[ToolDefinition] = Field(default_factory=list)
    skills: List[SkillDefinition] = Field(default_factory=list)
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list)


class BaseAgent:
    """
    Standardized Autonomous Agent instance.
    Encapsulates all assets found in an agent package folder:
    - config.json
    - prompt.md
    - tools.py
    - skills.json
    - mcp.json
    """

    def __init__(self, agent_dir: str):
        self.agent_dir = os.path.abspath(agent_dir)
        self.agent_id = os.path.basename(self.agent_dir)

        self.config: AgentConfig = self._load_config()
        self.system_prompt: str = self._load_prompt()
        self.tools: List[ToolDefinition] = []
        self.tool_handlers: Dict[str, Callable] = {}
        self._load_tools()
        self.skills: List[SkillDefinition] = self._load_skills()
        self.mcp_servers: List[MCPServerConfig] = self._load_mcp()

    def _load_config(self) -> AgentConfig:
        config_path = os.path.join(self.agent_dir, "config.json")
        if os.path.isfile(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return AgentConfig(**data)
            except Exception as e:
                print(f"Warning: Failed to load config.json in {self.agent_dir}: {e}")

        # Fallback config
        return AgentConfig(
            id=self.agent_id,
            name=self.agent_id.replace("_", " ").title(),
            role="Specialized Autonomous Agent",
            status="active",
        )

    def _load_prompt(self) -> str:
        prompt_path = os.path.join(self.agent_dir, "prompt.md")
        if os.path.isfile(prompt_path):
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Failed to load prompt.md in {self.agent_dir}: {e}")

        txt_path = os.path.join(self.agent_dir, "system_prompt.txt")
        if os.path.isfile(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Warning: Failed to load system_prompt.txt in {self.agent_dir}: {e}")

        return f"You are {self.config.name}, a helpful AI assistant in an agent swarm."

    def _load_tools(self) -> None:
        tools_path = os.path.join(self.agent_dir, "tools.py")
        if not os.path.isfile(tools_path):
            return

        try:
            module_name = f"agent_tools_{self.agent_id}"
            spec = importlib.util.spec_from_file_location(module_name, tools_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 1. Look for TOOLS list
                raw_tools = getattr(module, "TOOLS", [])
                loaded_tools = []
                for t in raw_tools:
                    if isinstance(t, ToolDefinition):
                        loaded_tools.append(t)
                    elif isinstance(t, dict):
                        loaded_tools.append(ToolDefinition(**t))
                self.tools = loaded_tools

                # 2. Look for TOOL_HANDLERS map
                handlers = getattr(module, "TOOL_HANDLERS", {})
                if isinstance(handlers, dict):
                    self.tool_handlers = handlers
        except Exception as e:
            print(f"Warning: Failed to load tools.py in {self.agent_dir}: {e}")

    def _load_skills(self) -> List[SkillDefinition]:
        skills_path = os.path.join(self.agent_dir, "skills.json")
        if not os.path.isfile(skills_path):
            return []

        try:
            with open(skills_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [SkillDefinition(**item) for item in data]
        except Exception as e:
            print(f"Warning: Failed to load skills.json in {self.agent_dir}: {e}")
        return []

    def _load_mcp(self) -> List[MCPServerConfig]:
        mcp_path = os.path.join(self.agent_dir, "mcp.json")
        if not os.path.isfile(mcp_path):
            return []

        try:
            with open(mcp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                servers = data.get("servers", [])
                if isinstance(servers, list):
                    return [MCPServerConfig(**s) for s in servers]
        except Exception as e:
            print(f"Warning: Failed to load mcp.json in {self.agent_dir}: {e}")
        return []

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Executes a registered python tool handler for this agent."""
        if tool_name in self.tool_handlers:
            handler = self.tool_handlers[tool_name]
            try:
                return handler(**args)
            except Exception as e:
                return {"error": f"Tool execution failed: {str(e)}"}
        return {"error": f"Tool '{tool_name}' not registered for agent '{self.agent_id}'"}

    def execute_mcp_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes an MCP server tool call via the centralized MCPManager."""
        from app.mcp.manager import mcp_manager
        configured_server_names = [s.name for s in self.mcp_servers]
        if configured_server_names and server_name not in configured_server_names:
            return {
                "isError": True,
                "error": f"MCP server '{server_name}' is not configured for agent '{self.agent_id}'. Configured: {configured_server_names}",
            }
        return mcp_manager.execute(server_name, tool_name, arguments)

    def to_profile(self) -> AgentProfile:
        """Generates a complete serialized AgentProfile."""
        return AgentProfile(
            id=self.config.id,
            name=self.config.name,
            role=self.config.role,
            status=self.config.status,
            system_prompt=self.system_prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            is_orchestrator=self.config.is_orchestrator,
            icon=self.config.icon,
            description=self.config.description or self.config.role,
            tools=self.tools,
            skills=self.skills,
            mcp_servers=self.mcp_servers,
        )
