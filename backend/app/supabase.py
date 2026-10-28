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

memory_store = MemoryStore()
