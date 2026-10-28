# Frontend Architectural Plan: Modular Agent Swarm, Tools, Skills & MCP Visualization

*Created: 2026-10-28T17:20:00+05:30*

> **Notice**: As per user instruction, this document details the thorough architectural design and component specifications for the frontend changes. Implementation code will NOT be written during this phase and will be executed only when explicitly requested.

---

## 1. Domain Data Models & Types (`frontend/src/app/chat/types.ts`)

The existing `Agent` interface in the frontend currently only possesses `id`, `name`, `role`, `status`, and `system_prompt`. We will extend it with rich metadata exposed by the backend `AgentRegistry`:

```typescript
export interface AgentTool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  handler_name?: string;
}

export interface AgentSkill {
  id: string;
  name: string;
  description: string;
  triggers: string[];
}

export interface AgentMCPServer {
  name: string;
  transport: 'stdio' | 'sse';
  command?: string;
  args?: string[];
  url?: string;
  tools: string[];
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  status: 'active' | 'busy' | 'idle' | 'offline';
  system_prompt?: string;
  // Extended modular properties
  model?: string;
  temperature?: number;
  is_orchestrator?: boolean;
  icon?: string;
  description?: string;
  tools?: AgentTool[];
  skills?: AgentSkill[];
  mcp_servers?: AgentMCPServer[];
}
```

---

## 2. UI Component Plans & Wireframes

### A. Swarm Roster Enhancement (`SessionSidebar.tsx`)

#### Objectives:
- Pin the **Orchestrator** at the top of the roster with an exclusive glowing crown badge (`bg-primary/20 text-primary border border-primary/40`).
- Display all 6 agents (`Orchestrator`, `Researcher`, `Coder`, `Reviewer`, `Data Analyst`, `Synthesizer`).
- Show compact chips for each agent indicating active tools count (e.g. `⚡ 3`) and MCP server count (e.g. `🔌 2`).
- Provide an info/inspect icon (`Info` or `ExternalLink`) on hover to trigger the **Agent Details Modal**.

#### Layout Wireframe:
```
+-------------------------------------------------------+
| ACTIVE SWARM (6)                                  [^] |
|                                                       |
| [★] Swarm Orchestrator (Auto)        (● Active)       |
|     Autonomous Coordinator & Dispatcher               |
|     [⚡ 2 Tools] [✦ 3 Skills]                        |
|                                                       |
| [🔍] Research Agent                   (● Active)       |
|     Deep investigation & Fact-checking               |
|     [⚡ 3 Tools] [🔌 1 MCP] [Info]                   |
|                                                       |
| [💻] Coder Agent                      (● Active)       |
|     Production software & Architecture                |
|     [⚡ 3 Tools] [🔌 2 MCP] [Info]                   |
|                                                       |
| [🛡️] Reviewer / QA Agent              (● Active)       |
|     Security audits & Code verification               |
|     [⚡ 3 Tools] [Info]                              |
|                                                       |
| [📊] Data Analyst Agent               (● Active)       |
|     Metrics, Aggregations & Analytics                |
|     [⚡ 3 Tools] [🔌 1 MCP] [Info]                   |
|                                                       |
| [📝] Synthesizer Agent                (● Active)       |
|     Technical writing & Executive reports            |
|     [⚡ 3 Tools] [Info]                              |
+-------------------------------------------------------+
```

---

### B. Chat Header Target Selector (`ChatHeader.tsx`)

#### Objectives:
- Segment the target agent dropdown:
  1. Default Group: `Swarm Orchestrator (Auto Intelligent Routing)`
  2. Specialists Group: Grouped by operational domain (`Research & Analysis`, `Engineering & QA`, `Synthesis`).
- Display agent capabilities count in the dropdown label.

---

### C. Message Feed & Delegation Visualization (`MessageItem.tsx`)

#### Objectives:
- When a response is orchestrated:
  - Display an **Orchestration Trace Banner**:
    `⚡ Orchestrator dispatched to Coder Agent (gemini-2.5-flash · 380ms)`
- In Tool Calls Accordion:
  - Distinguish between **Local Python Tool** (e.g. `[Local Tool: syntax_validator]`) and **MCP Server Tool** (e.g. `[MCP: filesystem.read_file]`).
  - Add execution status badges (`Success`, `Cached`, `Error`).

---

### D. New Component: Agent Details Modal (`AgentDetailsModal.tsx`)

#### Objectives:
- An accessible modal dialog with backdrop blur triggered by clicking any agent in the roster.
- **Tabs**:
  1. **Overview & Prompt**: Agent role, description, model parameters (`temperature`, `model`), and rendered markdown system prompt preview.
  2. **Tools (x)**: Expandable cards for each tool showing name, description, and parameter JSON schema.
  3. **Skills (x)**: Skill names, explanations, and trigger keyword tags.
  4. **MCP Servers (x)**: Connected servers, transport protocol (`stdio` / `sse`), and exposed MCP tools list.

#### Visual Wireframe:
```
+-------------------------------------------------------------------+
| [💻] Coder Agent · Profile & Capabilities                   [X]   |
+-------------------------------------------------------------------+
| Model: gemini-2.5-flash | Temp: 0.2 | Status: Active | MCP: Ready |
+-------------------------------------------------------------------+
| [ Overview & Prompt ]  [ Tools (3) ]  [ Skills (3) ]  [ MCP (2) ] |
+-------------------------------------------------------------------+
| > SYSTEM PROMPT                                                   |
|   You are the Coder Agent in an autonomous AI agent swarm...       |
|                                                                   |
| > REGISTERED TOOLS                                                |
|   • syntax_validator(code: str, language: str)                    |
|   • generate_test_suite(module: str, framework: str)              |
|   • diff_patcher(original: str, modified: str)                    |
|                                                                   |
| > MODEL CONTEXT PROTOCOL (MCP)                                    |
|   • Server: "filesystem" (stdio via @modelcontextprotocol)        |
|     Exposed tools: read_file, write_file, list_dir                |
|   • Server: "git" (stdio via mcp-server-git)                      |
|     Exposed tools: git_status, git_diff                           |
+-------------------------------------------------------------------+
| [ Close Profile ]                                                 |
+-------------------------------------------------------------------+
```

---

## 3. Implementation Phasing for Frontend

Once backend implementation is completed and approved, the frontend changes can be rolled out cleanly in 3 modular phases:
1. **Phase F1**: Update `types.ts` and fetch rich agent details in `chat/page.tsx`.
2. **Phase F2**: Update `SessionSidebar.tsx` and `ChatHeader.tsx` to display the new 6-agent roster and orchestrator pinning.
3. **Phase F3**: Create `AgentDetailsModal.tsx` and integrate tool/MCP/delegation badges into `MessageItem.tsx`.
