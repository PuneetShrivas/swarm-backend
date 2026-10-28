export interface ToolCall {
  tool: string;
  args?: Record<string, unknown>;
  result?: unknown;
}

export interface MessageMetadata {
  agent_state?: string;
  tool_calls?: ToolCall[];
  agent_id?: string;
  target_agent_id?: string;
  tokens_used?: number;
  [key: string]: unknown;
}

export interface ChatNode {
  id: string;
  parentId: string | null;
  childrenIds: string[];
  role: 'user' | 'agent' | 'system';
  content: string;
  metadata?: MessageMetadata;
  rating?: 'up' | 'down' | null;
  ratingComment?: string;
  createdAt: number;
}

export interface ConversationState {
  nodes: Record<string, ChatNode>;
  rootId: string | null;
  currentLeafId: string | null;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  status: string;
}

/**
 * Creates the initial conversation tree with a default greeting.
 */
export function createInitialState(
  greeting: string = 'Hello! I am part of the agent swarm. How can I help you today?'
): ConversationState {
  const greetingId = 'root-greeting';
  const initialNode: ChatNode = {
    id: greetingId,
    parentId: null,
    childrenIds: [],
    role: 'agent',
    content: greeting,
    createdAt: Date.now(),
    metadata: {
      agent_state: 'idle',
    },
  };

  return {
    nodes: {
      [greetingId]: initialNode,
    },
    rootId: greetingId,
    currentLeafId: greetingId,
  };
}

/**
 * Traverses from currentLeafId upwards to rootId to extract the active linear thread.
 */
export function getActivePath(
  nodes: Record<string, ChatNode>,
  currentLeafId: string | null
): ChatNode[] {
  if (!currentLeafId || !nodes[currentLeafId]) {
    return [];
  }

  const path: ChatNode[] = [];
  let curr: ChatNode | null = nodes[currentLeafId] || null;

  while (curr) {
    path.unshift(curr);
    if (!curr.parentId) break;
    curr = nodes[curr.parentId] || null;
  }

  return path;
}

/**
 * Finds sibling version info (e.g. index 1 of 2) for branching navigation.
 */
export function getSiblingInfo(
  nodes: Record<string, ChatNode>,
  nodeId: string
): { index: number; total: number; siblingIds: string[] } {
  const node = nodes[nodeId];
  if (!node) {
    return { index: 1, total: 1, siblingIds: [nodeId] };
  }

  // If node has a parent, siblings are parent's children
  if (node.parentId && nodes[node.parentId]) {
    const siblingIds = nodes[node.parentId].childrenIds;
    const idx = siblingIds.indexOf(nodeId);
    return {
      index: idx >= 0 ? idx + 1 : 1,
      total: siblingIds.length,
      siblingIds,
    };
  }

  // Root level node
  return {
    index: 1,
    total: 1,
    siblingIds: [nodeId],
  };
}

/**
 * Finds the latest leaf downstream from a given node following the last child.
 */
export function findLatestLeaf(
  nodes: Record<string, ChatNode>,
  nodeId: string
): string {
  let curr = nodes[nodeId];
  if (!curr) return nodeId;

  while (curr.childrenIds && curr.childrenIds.length > 0) {
    const lastChildId = curr.childrenIds[curr.childrenIds.length - 1];
    const nextNode = nodes[lastChildId];
    if (!nextNode) break;
    curr = nextNode;
  }

  return curr.id;
}

/**
 * Switches the active branch to a target sibling node.
 */
export function switchBranch(
  state: ConversationState,
  targetSiblingId: string
): ConversationState {
  if (!state.nodes[targetSiblingId]) return state;
  const newLeafId = findLatestLeaf(state.nodes, targetSiblingId);
  return {
    ...state,
    currentLeafId: newLeafId,
  };
}

/**
 * Adds a new message node to the tree as a child of parentId.
 */
export function addMessageNode(
  state: ConversationState,
  role: 'user' | 'agent' | 'system',
  content: string,
  parentId: string | null,
  metadata?: MessageMetadata
): { newState: ConversationState; newNodeId: string } {
  const id = `msg-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  const newNode: ChatNode = {
    id,
    parentId,
    childrenIds: [],
    role,
    content,
    metadata,
    createdAt: Date.now(),
  };

  const updatedNodes = { ...state.nodes, [id]: newNode };

  if (parentId && updatedNodes[parentId]) {
    const parent = updatedNodes[parentId];
    updatedNodes[parentId] = {
      ...parent,
      childrenIds: [...parent.childrenIds, id],
    };
  }

  return {
    newState: {
      nodes: updatedNodes,
      rootId: state.rootId || id,
      currentLeafId: id,
    },
    newNodeId: id,
  };
}

/**
 * Sets rating (thumbs up / thumbs down) for a specific node.
 */
export function setNodeRating(
  state: ConversationState,
  nodeId: string,
  rating: 'up' | 'down' | null
): ConversationState {
  if (!state.nodes[nodeId]) return state;

  return {
    ...state,
    nodes: {
      ...state.nodes,
      [nodeId]: {
        ...state.nodes[nodeId],
        rating,
      },
    },
  };
}

/**
 * Exports the active thread to Markdown format.
 */
export function exportToMarkdown(path: ChatNode[]): string {
  let md = `# Swarm Chat Transcript\n*Exported on ${new Date().toLocaleString()}*\n\n---\n\n`;

  path.forEach((node, i) => {
    const speaker = node.role === 'user' ? '🧑 **User**' : '🤖 **Agent Swarm**';
    md += `### ${speaker}\n\n${node.content}\n\n`;

    if (node.metadata?.tool_calls && node.metadata.tool_calls.length > 0) {
      md += `*Tool Calls:*\n\`\`\`json\n${JSON.stringify(node.metadata.tool_calls, null, 2)}\n\`\`\`\n\n`;
    }

    if (node.rating) {
      md += `*Rating: ${node.rating === 'up' ? '👍 Upvoted' : '👎 Downvoted'}*\n\n`;
    }

    if (i < path.length - 1) {
      md += `---\n\n`;
    }
  });

  return md;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface DBMessage {
  id: string;
  session_id: string;
  user_id: string;
  parent_id: string | null;
  role: 'user' | 'agent' | 'system';
  content: string;
  metadata?: MessageMetadata;
  rating?: 'up' | 'down' | null;
  created_at: string;
}

export interface UserUsageSummary {
  total_tokens: number;
  total_requests: number;
  models: Record<string, number>;
  agents: Record<string, number>;
  recent_activity: Array<{
    id: string;
    model: string;
    agent_id: string;
    total_tokens: number;
    latency_ms?: number;
    created_at: string;
  }>;
}

/**
 * Reconstructs the multi-branch ConversationState tree from flat DB messages.
 */
export function reconstructTreeFromMessages(
  messages: DBMessage[],
  defaultGreeting: string = 'Hello! I am part of the agent swarm. How can I help you today?'
): ConversationState {
  if (!messages || messages.length === 0) {
    return createInitialState(defaultGreeting);
  }

  const nodes: Record<string, ChatNode> = {};

  messages.forEach((m) => {
    nodes[m.id] = {
      id: m.id,
      parentId: m.parent_id,
      childrenIds: [],
      role: m.role,
      content: m.content,
      metadata: m.metadata || {},
      rating: m.rating,
      createdAt: new Date(m.created_at).getTime() || Date.now(),
    };
  });

  let rootId: string | null = null;
  let lastLeafId: string | null = null;

  messages.forEach((m) => {
    if (m.parent_id && nodes[m.parent_id]) {
      if (!nodes[m.parent_id].childrenIds.includes(m.id)) {
        nodes[m.parent_id].childrenIds.push(m.id);
      }
    } else if (!rootId) {
      rootId = m.id;
    }
    lastLeafId = m.id;
  });

  if (!rootId && messages.length > 0) {
    rootId = messages[0].id;
  }

  return {
    nodes,
    rootId,
    currentLeafId: lastLeafId || rootId,
  };
}
