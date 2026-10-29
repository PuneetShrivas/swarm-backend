"""
Knowledge Base MCP entrypoint.
Supports stdio execution for `python -m app.mcp.knowledge`.
"""

import sys
import json
from app.mcp.manager import mcp_manager


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        result = mcp_manager.execute("knowledge-base", cmd, args)
        print(json.dumps(result, indent=2))
        return

    tools = mcp_manager.get_server_tools("knowledge-base")
    print(json.dumps({"server": "knowledge-base", "status": "running", "tools": tools}, indent=2))


if __name__ == "__main__":
    main()
