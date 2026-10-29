from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def current_iso_time() -> str:
    return datetime.now(timezone.utc).isoformat()


# -------------------------------------------------------------
# User Custom Agent Models
# -------------------------------------------------------------
class UserAgentProfile(BaseModel):
    id: str = Field(..., description="Unique agent identifier (e.g. agent-sales-analyst)")
    user_id: Optional[str] = Field(None, description="Owner user ID")
    name: str = Field(..., description="Display name of the agent")
    role: str = Field("Specialist", description="Role specialization")
    description: str = Field("", description="Detailed agent summary")
    system_prompt: str = Field(..., description="System instructions and persona guidelines")
    model: str = Field("qwen-3.8", description="Underlying model identifier")
    temperature: float = Field(0.3, ge=0.0, le=2.0, description="Sampling temperature")
    icon: str = Field("Bot", description="Lucide icon identifier")
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="Associated tool definitions")
    skills: List[Dict[str, Any]] = Field(default_factory=list, description="Skill capabilities")
    is_public: bool = Field(False, description="Whether available for other users")
    created_at: Optional[str] = Field(default_factory=current_iso_time)
    updated_at: Optional[str] = Field(default_factory=current_iso_time)


# -------------------------------------------------------------
# Python Script Tool Models
# -------------------------------------------------------------
class ScriptTool(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    name: str = Field(..., description="Identifier name of the script tool")
    description: str = Field("", description="What this script performs")
    code: str = Field(..., description="Python source code containing def execute(input_data, context):")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for tool input arguments")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for output dictionary")
    is_public: bool = Field(False, description="Whether this tool can be used by other users")
    created_at: Optional[str] = Field(default_factory=current_iso_time)
    updated_at: Optional[str] = Field(default_factory=current_iso_time)


class ScriptToolTestRequest(BaseModel):
    input_data: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ScriptToolTestResponse(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    stdout: Optional[str] = None
    duration_ms: float = 0.0
    error: Optional[str] = None


# -------------------------------------------------------------
# Knowledge Base Document Models
# -------------------------------------------------------------
class KnowledgeFile(BaseModel):
    id: Optional[str] = None
    workflow_id: str
    user_id: Optional[str] = None
    file_name: str
    file_type: str = "text/plain"
    file_size: int = 0
    content_text: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = Field(default_factory=current_iso_time)


# -------------------------------------------------------------
# Workflow Definition Models
# -------------------------------------------------------------
class WorkflowStep(BaseModel):
    id: str = Field(..., description="Unique step ID within workflow (e.g. step_1)")
    name: str = Field(..., description="Human readable step name")
    step_type: str = Field(default="agent", description="'agent', 'condition', 'python_code', 'loop', 'artifact'")
    agent_id: Optional[str] = Field(default="orchestrator", description="Assigned agent ID (prebuilt or custom)")
    model: Optional[str] = Field(default=None, description="Optional LLM model override, e.g. 'sonar', 'qwen-3.8'")
    instructions: Optional[str] = Field(default="", description="Step instructions with template variables like {{inputs.x}}")
    code: Optional[str] = Field(default="", description="Python source code containing def execute(inputs, previous_outputs, context):")
    condition_expr: Optional[str] = Field(default="", description="Expression, e.g. {{steps.step_1.output.score}} >= 80")
    true_target_step_id: Optional[str] = Field(default=None, description="Step ID to jump to if True")
    false_target_step_id: Optional[str] = Field(default=None, description="Step ID to jump to if False")
    loop_target_step_id: Optional[str] = Field(default=None, description="Step ID to loop back to")
    max_loop_iterations: int = Field(default=3, description="Maximum loop iterations before break")
    artifact_title: Optional[str] = Field(default=None, description="Title of the created artifact")
    artifact_type: Optional[str] = Field(default="markdown", description="'markdown', 'code', 'json', 'report'")
    tool_ids: List[str] = Field(default_factory=list, description="IDs of script tools attached to this step")
    knowledge_file_ids: List[str] = Field(default_factory=list, description="IDs of knowledge files attached to this step")
    depends_on: List[str] = Field(default_factory=list, description="Step IDs this step depends upon")
    input_mapping: Dict[str, str] = Field(default_factory=dict, description="Variable mappings")
    position: Optional[Dict[str, float]] = Field(default=None, description="Position coordinates in React Flow graph")


class Workflow(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    title: str = Field(..., description="Workflow title")
    description: str = Field("", description="Detailed workflow overview")
    goal: str = Field(..., description="High-level objective / goal of the workflow")
    steps: List[WorkflowStep] = Field(default_factory=list, description="Ordered steps or DAG nodes")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="React Flow graph edges")
    visibility: str = Field("private", description="'private', 'shared', or 'public'")
    share_slug: Optional[str] = Field(None, description="Unique slug for shared viewing")
    created_at: Optional[str] = Field(default_factory=current_iso_time)
    updated_at: Optional[str] = Field(default_factory=current_iso_time)


class WorkflowCreateUpdatePayload(BaseModel):
    title: str
    description: Optional[str] = ""
    goal: str
    steps: List[WorkflowStep] = Field(default_factory=list)
    edges: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    visibility: Optional[str] = "private"


# -------------------------------------------------------------
# Execution & Testing Models
# -------------------------------------------------------------
class StepUnitTestRequest(BaseModel):
    step_id: str
    mock_inputs: Dict[str, Any] = Field(default_factory=dict)
    mock_previous_outputs: Dict[str, Any] = Field(default_factory=dict)


class StepUnitTestResponse(BaseModel):
    status: str
    step_id: str
    agent_id: str
    prompt_rendered: str
    output_data: Dict[str, Any]
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = 0
    duration_ms: float = 0.0
    error: Optional[str] = None


class WorkflowRunRequest(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None


class WorkflowStepRun(BaseModel):
    id: Optional[str] = None
    run_id: str
    step_id: str
    step_index: int = 0
    agent_id: str
    status: str = "pending"  # pending, running, completed, failed, skipped
    prompt_rendered: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = 0
    duration_ms: float = 0.0
    error: Optional[str] = None
    created_at: Optional[str] = Field(default_factory=current_iso_time)
    completed_at: Optional[str] = None


class WorkflowRun(BaseModel):
    id: Optional[str] = None
    workflow_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    trigger_type: str = "manual"  # manual, unit_test, system_test, chat
    status: str = "queued"  # queued, running, completed, failed, cancelled
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    total_tokens: int = 0
    duration_ms: float = 0.0
    error: Optional[str] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="Artifacts generated by the workflow")
    created_at: Optional[str] = Field(default_factory=current_iso_time)
    completed_at: Optional[str] = None
    step_runs: Optional[List[WorkflowStepRun]] = Field(default_factory=list)
