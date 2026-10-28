import os
from typing import Dict, List, Optional
from app.agents.base import BaseAgent, AgentProfile


class AgentRegistry:
    """
    Dynamic filesystem scanner and singleton registry for all Swarm Agents.
    Scans `backend/app/agents/*/` for modular agent packages, parses their
    standardized assets, and manages runtime lookups and custom additions.
    """

    def __init__(self, agents_dir: Optional[str] = None):
        if agents_dir:
            self.agents_dir = os.path.abspath(agents_dir)
        else:
            self.agents_dir = os.path.dirname(os.path.abspath(__file__))

        self._agents: Dict[str, BaseAgent] = {}
        self._custom_agents: Dict[str, AgentProfile] = {}
        self._initialized: bool = False

    def initialize(self) -> None:
        """Discovers and loads all agent packages from the filesystem."""
        self._agents.clear()
        if not os.path.isdir(self.agents_dir):
            print(f"Warning: Agents directory not found at {self.agents_dir}")
            return

        for entry in os.scandir(self.agents_dir):
            if entry.is_dir() and not entry.name.startswith((".", "__")):
                config_file = os.path.join(entry.path, "config.json")
                prompt_file = os.path.join(entry.path, "prompt.md")

                # If either config.json or prompt.md exists, treat as an agent package
                if os.path.isfile(config_file) or os.path.isfile(prompt_file):
                    try:
                        agent = BaseAgent(entry.path)
                        self._agents[agent.config.id.lower()] = agent
                    except Exception as e:
                        print(f"Error loading agent package '{entry.name}': {e}")

        self._initialized = True

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """Lookup an agent by ID (case-insensitive)."""
        if not self._initialized:
            self.initialize()
        return self._agents.get(agent_id.lower())

    def get_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """Returns the AgentProfile for a filesystem or custom agent."""
        if not self._initialized:
            self.initialize()
        agent = self.get(agent_id)
        if agent:
            return agent.to_profile()
        return self._custom_agents.get(agent_id.lower())

    def get_all(self) -> List[AgentProfile]:
        """Returns all registered agent profiles (filesystem + custom)."""
        if not self._initialized:
            self.initialize()

        profiles = [agent.to_profile() for agent in self._agents.values()]
        # Append runtime custom agents
        for custom in self._custom_agents.values():
            if custom.id.lower() not in self._agents:
                profiles.append(custom)
        return profiles

    def get_orchestrator(self) -> Optional[BaseAgent]:
        """Finds the designated swarm orchestrator agent."""
        if not self._initialized:
            self.initialize()

        for agent in self._agents.values():
            if agent.config.is_orchestrator or agent.config.id.lower() == "orchestrator":
                return agent

        # Fallback to first available agent if no orchestrator flagged
        if self._agents:
            return next(iter(self._agents.values()))
        return None

    def register_custom(self, profile: AgentProfile) -> None:
        """Registers a dynamic custom agent into runtime memory."""
        self._custom_agents[profile.id.lower()] = profile

    def reload(self) -> None:
        """Forces re-scanning and re-parsing of all filesystem agent assets."""
        self.initialize()


# Global Singleton Registry Instance
agent_registry = AgentRegistry()
