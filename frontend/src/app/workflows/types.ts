// =========================================================
// Frontend Workflows TypeScript Definitions
// =========================================================

export type WorkflowStepType = "agent" | "condition" | "python_code" | "loop" | "artifact";

export interface WorkflowArtifact {
  title: string;
  type: string;
  content: string;
  step_id?: string;
  step_name?: string;
  created_at?: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  agent_id: string;
  instructions: string;
  tool_ids: string[];
  knowledge_file_ids: string[];
  attached_artifact_ids?: string[];
  depends_on: string[];
  position?: { x: number; y: number };
  step_type?: WorkflowStepType;
  code?: string;
  condition_expr?: string;
  true_target_step_id?: string;
  false_target_step_id?: string;
  loop_target_step_id?: string;
  max_loop_iterations?: number;
  artifact_title?: string;
  artifact_type?: string;
  model?: string;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string | null;
  targetHandle?: string | null;
  animated?: boolean;
}

export interface Workflow {
  id: string;
  user_id?: string;
  title: string;
  description: string;
  goal: string;
  steps: WorkflowStep[];
  edges: WorkflowEdge[];
  visibility: "private" | "shared" | "public";
  share_slug?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ScriptTool {
  id: string;
  user_id?: string;
  name: string;
  description: string;
  code: string;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  is_public: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface KnowledgeFile {
  id: string;
  workflow_id: string;
  user_id?: string;
  file_name: string;
  file_type: string;
  file_size: number;
  content_text: string;
  created_at?: string;
}

export interface CustomAgent {
  id: string;
  user_id?: string;
  name: string;
  role: string;
  description: string;
  system_prompt: string;
  model: string;
  temperature: number;
  icon: string;
  is_public: boolean;
  tools?: Array<Record<string, unknown>>;
  skills?: Array<Record<string, unknown>>;
  created_at?: string;
  updated_at?: string;
}

export interface WorkflowStepRun {
  id: string;
  run_id: string;
  step_id: string;
  step_index: number;
  agent_id: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  prompt_rendered?: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  tool_calls: Array<{
    tool_id?: string;
    tool_name?: string;
    status?: string;
    result?: unknown;
    stdout?: string;
    duration_ms?: number;
    error?: string;
  }>;
  tokens_used: number;
  duration_ms: number;
  error?: string | null;
  created_at?: string;
  completed_at?: string | null;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  user_id?: string;
  session_id?: string | null;
  trigger_type: "manual" | "unit_test" | "system_test" | "chat";
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  input_data: Record<string, unknown>;
  output_data: {
    goal?: string;
    final_result?: string;
    step_outputs?: Record<string, unknown>;
  };
  total_tokens: number;
  duration_ms: number;
  error?: string | null;
  artifacts?: WorkflowArtifact[];
  created_at: string;
  completed_at?: string | null;
  step_runs?: WorkflowStepRun[];
}

export interface StepUnitTestResponse {
  status: "completed" | "error";
  step_id: string;
  agent_id: string;
  prompt_rendered: string;
  step_type?: WorkflowStepType;
  branch_taken?: boolean;
  artifacts?: WorkflowArtifact[];
  output_data: Record<string, unknown>;
  tool_calls: Array<Record<string, unknown>>;
  tokens_used: number;
  duration_ms: number;
  error?: string | null;
}
