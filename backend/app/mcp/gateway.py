"""
Swarm Gateway MCP entrypoint.
Supports stdio execution for `python -m app.mcp.gateway`.
"""

import sys
import json
from app.mcp.manager import mcp_manager


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        result = mcp_manager.execute("swarm-gateway", cmd, args)
        print(json.dumps(result, indent=2))
        return

    # Fallback to listing registered tools
    tools = mcp_manager.get_server_tools("swarm-gateway")
    print(json.dumps({"server": "swarm-gateway", "status": "running", "tools": tools}, indent=2))


if __name__ == "__main__":
    main()
