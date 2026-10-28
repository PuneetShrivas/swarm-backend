import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "https://xyzcompany.supabase.co")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "public-anon-key")
SUPABASE_SERVICE_KEY: Optional[str] = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

def is_supabase_configured() -> bool:
    """Returns True if valid Supabase credentials have been supplied."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    if "xyzcompany.supabase.co" in SUPABASE_URL or SUPABASE_KEY == "public-anon-key":
        return False
    return True

# Initialize global base client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Warning: Failed to initialize base Supabase client: {e}")
    supabase = None

def get_user_supabase_client(token: Optional[str] = None) -> Optional[Client]:
    """Returns a client scoped with user's JWT for RLS enforcement."""
    if not is_supabase_configured():
        return None
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        if token:
            client.postgrest.auth(token)
        return client
    except Exception as e:
        print(f"Error creating user-scoped Supabase client: {e}")
        return None

# =====================================================================
# In-Memory Fallback Store (Used when Supabase is not configured)
# =====================================================================
class MemoryStore:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.messages: Dict[str, List[Dict[str, Any]]] = {}
        self.usage: Dict[str, List[Dict[str, Any]]] = {}
        self.user_agents: Dict[str, Dict[str, Any]] = {}
        self.workflow_tools: Dict[str, Dict[str, Any]] = {}
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.knowledge_files: Dict[str, Dict[str, Any]] = {}
        self.workflow_runs: Dict[str, Dict[str, Any]] = {}
        self.workflow_step_runs: Dict[str, List[Dict[str, Any]]] = {}

    def get_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        user_sessions = [s for s in self.sessions.values() if s.get("user_id") == user_id]
        return sorted(user_sessions, key=lambda s: s.get("updated_at", ""), reverse=True)

    def get_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        if s and s.get("user_id") == user_id:
            return s
        return None

    def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        self.sessions[session_data["id"]] = session_data
        if session_data["id"] not in self.messages:
            self.messages[session_data["id"]] = []
        return session_data

    def update_session(self, session_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        s = self.get_session(session_id, user_id)
        if not s:
            return None
        s.update(updates)
        return s

    def delete_session(self, session_id: str, user_id: str) -> bool:
        s = self.get_session(session_id, user_id)
        if not s:
            return False
        del self.sessions[session_id]
        self.messages.pop(session_id, None)
        return True

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        return self.messages.get(session_id, [])

    def add_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        session_id = message_data["session_id"]
        if session_id not in self.messages:
            self.messages[session_id] = []
        self.messages[session_id].append(message_data)
        # Touch session updated_at
        if session_id in self.sessions:
            self.sessions[session_id]["updated_at"] = message_data.get("created_at")
        return message_data

    def add_usage(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = usage_data["user_id"]
        if user_id not in self.usage:
            self.usage[user_id] = []
        self.usage[user_id].append(usage_data)
        return usage_data

    def get_usage(self, user_id: str) -> List[Dict[str, Any]]:
        return self.usage.get(user_id, [])

    # ---------------- User Custom Agents ----------------
    def get_user_agents(self, user_id: str) -> List[Dict[str, Any]]:
        agents = [
            a for a in self.user_agents.values()
            if a.get("user_id") == user_id or a.get("is_public")
        ]
        return sorted(agents, key=lambda a: a.get("updated_at", ""), reverse=True)

    def get_user_agent(self, agent_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        a = self.user_agents.get(agent_id.lower())
        if not a:
            return None
        if user_id and a.get("user_id") != user_id and not a.get("is_public"):
            return None
        return a

    def create_user_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        aid = agent_data["id"].lower()
        self.user_agents[aid] = agent_data
        return agent_data

    def update_user_agent(self, agent_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        a = self.get_user_agent(agent_id, user_id)
        if not a:
            return None
        a.update(updates)
        return a

    def delete_user_agent(self, agent_id: str, user_id: str) -> bool:
        a = self.get_user_agent(agent_id, user_id)
        if not a:
            return False
        del self.user_agents[agent_id.lower()]
        return True

    # ---------------- Workflow Tools ----------------
    def get_tools(self, user_id: str) -> List[Dict[str, Any]]:
        tools = [
            t for t in self.workflow_tools.values()
            if t.get("user_id") == user_id or t.get("is_public")
        ]
        return sorted(tools, key=lambda t: t.get("updated_at", ""), reverse=True)

    def get_tool(self, tool_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        t = self.workflow_tools.get(tool_id)
        if not t:
            return None
        if user_id and t.get("user_id") != user_id and not t.get("is_public"):
            return None
        return t

    def create_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        self.workflow_tools[tool_data["id"]] = tool_data
        return tool_data

    def update_tool(self, tool_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        t = self.get_tool(tool_id, user_id)
        if not t:
            return None
        t.update(updates)
        return t

    def delete_tool(self, tool_id: str, user_id: str) -> bool:
        t = self.get_tool(tool_id, user_id)
        if not t:
            return False
        del self.workflow_tools[tool_id]
        return True

    # ---------------- Workflows ----------------
    def get_workflows(self, user_id: str) -> List[Dict[str, Any]]:
        wfs = [
            w for w in self.workflows.values()
            if w.get("user_id") == user_id or w.get("visibility") in ("shared", "public")
        ]
        return sorted(wfs, key=lambda w: w.get("updated_at", ""), reverse=True)

    def get_workflow(self, workflow_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        w = self.workflows.get(workflow_id)
        if not w:
            return None
        if user_id and w.get("user_id") != user_id and w.get("visibility") not in ("shared", "public"):
            return None
        return w

    def get_shared_workflow(self, share_slug: str) -> Optional[Dict[str, Any]]:
        for w in self.workflows.values():
            if w.get("share_slug") == share_slug and w.get("visibility") in ("shared", "public"):
                return w
        return None

    def create_workflow(self, wf_data: Dict[str, Any]) -> Dict[str, Any]:
        self.workflows[wf_data["id"]] = wf_data
        return wf_data

    def update_workflow(self, workflow_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        w = self.workflows.get(workflow_id)
        if not w or w.get("user_id") != user_id:
            return None
        w.update(updates)
        return w

    def delete_workflow(self, workflow_id: str, user_id: str) -> bool:
        w = self.workflows.get(workflow_id)
        if not w or w.get("user_id") != user_id:
            return False
        del self.workflows[workflow_id]
        # Clean up related runs and knowledge
        to_del_k = [kid for kid, k in self.knowledge_files.items() if k.get("workflow_id") == workflow_id]
        for kid in to_del_k:
            del self.knowledge_files[kid]
        return True

    # ---------------- Knowledge Base Files ----------------
    def get_knowledge_files(self, workflow_id: str) -> List[Dict[str, Any]]:
        files = [f for f in self.knowledge_files.values() if f.get("workflow_id") == workflow_id]
        return sorted(files, key=lambda f: f.get("created_at", ""), reverse=False)

    def add_knowledge_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        self.knowledge_files[file_data["id"]] = file_data
        return file_data

    def delete_knowledge_file(self, file_id: str, user_id: str) -> bool:
        f = self.knowledge_files.get(file_id)
        if not f or f.get("user_id") != user_id:
            return False
        del self.knowledge_files[file_id]
        return True

    # ---------------- Workflow Runs & Step Runs ----------------
    def create_workflow_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        self.workflow_runs[run_data["id"]] = run_data
        if run_data["id"] not in self.workflow_step_runs:
            self.workflow_step_runs[run_data["id"]] = []
        return run_data

    def update_workflow_run(self, run_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        r = self.workflow_runs.get(run_id)
        if not r:
            return None
        r.update(updates)
        return r

    def get_workflow_runs(self, workflow_id: str) -> List[Dict[str, Any]]:
        runs = [r for r in self.workflow_runs.values() if r.get("workflow_id") == workflow_id]
        return sorted(runs, key=lambda r: r.get("created_at", ""), reverse=True)

    def get_workflow_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self.workflow_runs.get(run_id)

    def add_step_run(self, step_run_data: Dict[str, Any]) -> Dict[str, Any]:
        rid = step_run_data["run_id"]
        if rid not in self.workflow_step_runs:
            self.workflow_step_runs[rid] = []
        self.workflow_step_runs[rid].append(step_run_data)
        return step_run_data

    def get_step_runs(self, run_id: str) -> List[Dict[str, Any]]:
        runs = self.workflow_step_runs.get(run_id, [])
        return sorted(runs, key=lambda s: s.get("step_index", 0))

memory_store = MemoryStore()
