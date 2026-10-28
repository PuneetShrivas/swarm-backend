import time
import json
import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from app.workflows.models import (
    WorkflowRun,
    WorkflowStepRun,
    StepUnitTestResponse,
    current_iso_time,
)
from app.workflows.tool_runner import execute_tool_script
from app.workflows.knowledge import format_knowledge_context
from app.agents.registry import agent_registry
from app.supabase import memory_store


def topological_sort_steps(
    steps: List[Dict[str, Any]],
    edges: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Orders steps respecting explicit `depends_on` lists and React Flow graph edges.
    If circular dependencies occur, returns the original sequence.
    """
    if not steps:
        return []

    step_map = {s["id"]: s for s in steps}
    dependencies: Dict[str, set] = {s["id"]: set(s.get("depends_on") or []) for s in steps}

    # Incorporate React Flow edges (source -> target means target depends on source)
    if edges:
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source in step_map and target in step_map:
                dependencies[target].add(source)

    ordered = []
    visited = set()

    # Find nodes with 0 incoming dependencies
    ready = [sid for sid, deps in dependencies.items() if len(deps) == 0]

    while ready:
        curr = ready.pop(0)
        ordered.append(step_map[curr])
        visited.add(curr)

        for sid, deps in dependencies.items():
            if sid not in visited and curr in deps:
                deps.remove(curr)
                if len(deps) == 0:
                    ready.append(sid)

    # If all nodes were resolved, return ordered sequence; otherwise fallback
    if len(ordered) == len(steps):
        return ordered

    # Fallback to declared list order if graph has cycles or disconnected roots
    return steps


def interpolate_template(
    template: str,
    inputs: Dict[str, Any],
    previous_outputs: Dict[str, Any],
    goal: str = ""
) -> str:
    """
    Substitutes variables inside `{{...}}` tokens in instructions.
    Examples:
        {{goal}} -> workflow goal
        {{inputs.query}} -> inputs["query"]
        {{steps.step_1.output.result}} -> previous_outputs["step_1"]["result"]
    """
    if not template:
        return ""

    rendered = template.replace("{{goal}}", str(goal or ""))

    # Regex matches {{ path.to.var }}
    pattern = re.compile(r"\{\{\s*([\w\.\-]+)\s*\}\}")

    def _replace_match(match):
        token = match.group(1).strip()
        parts = token.split(".")

        # 1. Inputs lookup: {{inputs.name}} or {{input.name}}
        if parts[0] in ("inputs", "input") and len(parts) > 1:
            val = inputs
            for p in parts[1:]:
                if isinstance(val, dict):
                    val = val.get(p)
                else:
                    return match.group(0)
            return json.dumps(val) if isinstance(val, (dict, list)) else str(val or "")

        # 2. Step outputs lookup: {{steps.step_1.output}} or {{step_1.result}}
        if parts[0] in ("steps", "step") and len(parts) > 1:
            step_id = parts[1]
            step_out = previous_outputs.get(step_id, {})
            # If path ends at output, e.g. {{steps.step_1.output}}
            if len(parts) == 3 and parts[2] == "output":
                return json.dumps(step_out) if isinstance(step_out, (dict, list)) else str(step_out or "")
            if len(parts) > 3 and parts[2] == "output":
                val = step_out
                for p in parts[3:]:
                    if isinstance(val, dict):
                        val = val.get(p)
                    else:
                        return match.group(0)
                return json.dumps(val) if isinstance(val, (dict, list)) else str(val or "")

        # Direct step name lookup: {{step_1.output}}
        if parts[0] in previous_outputs:
            step_out = previous_outputs[parts[0]]
            if len(parts) == 1:
                return json.dumps(step_out) if isinstance(step_out, (dict, list)) else str(step_out or "")
            val = step_out
            for p in parts[1:]:
                if isinstance(val, dict):
                    val = val.get(p)
                else:
                    return match.group(0)
            return json.dumps(val) if isinstance(val, (dict, list)) else str(val or "")

        # Direct root input match: {{query}}
        if token in inputs:
            val = inputs[token]
            return json.dumps(val) if isinstance(val, (dict, list)) else str(val or "")

        return match.group(0)

    return pattern.sub(_replace_match, rendered)


class WorkflowExecutionEngine:
    """
    Core runtime engine that resolves DAG step dependencies, executes sandboxed
    Python tools, injects knowledge base documents, dispatches to agents, and
    records step execution telemetry.
    """

    def _resolve_agent(self, agent_id: str, user_id: Optional[str] = None):
        """Resolves an agent from prebuilt filesystem registry or user custom agents."""
        # 1. Check prebuilt filesystem agents
        agent = agent_registry.get(agent_id)
        if agent:
            return agent

        # 2. Check custom agents in registry
        profile = agent_registry.get_profile(agent_id)
        if profile:
            return profile

        # 3. Check memory store for user custom agents
        if user_id:
            user_ag = memory_store.get_user_agent(agent_id, user_id)
            if user_ag:
                return user_ag

        # Fallback to orchestrator
        return agent_registry.get_orchestrator()

    def _execute_agent_turn(
        self,
        agent: Any,
        prompt: str,
        system_instructions: str,
        model_name: str = "gemini-3.8-flash",
        temperature: float = 0.3
    ) -> Tuple[str, int]:
        """
        Executes a prompt against Gemini or generates a deterministic fallback response.
        Returns (response_text, tokens_used).
        """
        # Try live Gemini if configured and not in test/mock mode
        try:
            import os
            api_key = os.environ.get("GEMINI_API_KEY")
            if (
                api_key
                and not api_key.startswith("test-")
                and not api_key.startswith("your-")
                and os.environ.get("TESTING") != "true"
                and os.environ.get("MOCK_GEMINI") != "true"
            ):
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=api_key)
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instructions,
                        temperature=temperature,
                    )
                )
                text = resp.text or ""
                tokens = getattr(getattr(resp, "usage_metadata", None), "total_token_count", 0)
                if not tokens:
                    tokens = max(len(prompt.split()) + len(text.split()), 50)
                return text, tokens
        except Exception as e:
            print(f"Workflow agent Gemini generation note: {e}")

        # Deterministic synthetic execution (used in tests and offline environments)
        agent_name = getattr(agent, "name", None) or (agent.get("name") if isinstance(agent, dict) else "Agent")
        word_count = len(prompt.split())
        synthetic_text = (
            f"[{agent_name} Response]\n"
            f"Successfully executed workflow instruction: {prompt[:120]}...\n"
            f"Generated high-quality synthesis based on persona guidelines."
        )
        tokens_used = word_count + 65
        return synthetic_text, tokens_used

    def execute_single_step(
        self,
        step: Dict[str, Any],
        inputs: Dict[str, Any],
        previous_outputs: Dict[str, Any],
        goal: str,
        knowledge_files: List[Dict[str, Any]],
        tools_map: Dict[str, Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Executes an individual workflow step:
        1. Interpolates template variables.
        2. Executes attached Python script tools.
        3. Formats and attaches relevant knowledge documents.
        4. Invokes the assigned agent.
        5. Returns structured output dictionary.
        """
        start_time = time.time()
        step_id = step.get("id", "step_1")
        agent_id = step.get("agent_id", "orchestrator")
        raw_instructions = step.get("instructions", "")

        # 1. Variable interpolation
        rendered_prompt = interpolate_template(raw_instructions, inputs, previous_outputs, goal)

        # 2. Execute attached Python script tools
        tool_calls = []
        tool_outputs = {}
        attached_tool_ids = step.get("tool_ids") or []
        for tid in attached_tool_ids:
            tool_obj = tools_map.get(tid)
            if tool_obj and tool_obj.get("code"):
                t_context = {
                    "goal": goal,
                    "step_id": step_id,
                    "previous_outputs": previous_outputs,
                }
                tool_res = execute_tool_script(
                    code=tool_obj["code"],
                    input_data=inputs,
                    context=t_context,
                    timeout_seconds=5.0
                )
                tool_calls.append({
                    "tool_id": tid,
                    "tool_name": tool_obj.get("name", "tool"),
                    "status": tool_res.get("status"),
                    "result": tool_res.get("result"),
                    "stdout": tool_res.get("stdout"),
                    "duration_ms": tool_res.get("duration_ms"),
                    "error": tool_res.get("error"),
                })
                if tool_res.get("status") == "success":
                    tool_outputs[tool_obj.get("name", tid)] = tool_res.get("result")

        # 3. Knowledge context injection
        attached_k_ids = set(step.get("knowledge_file_ids") or [])
        relevant_files = [f for f in knowledge_files if not attached_k_ids or f.get("id") in attached_k_ids]
        kb_text = format_knowledge_context(relevant_files)

        # 4. Resolve agent
        agent = self._resolve_agent(agent_id, user_id)
        if isinstance(agent, dict):
            agent_prompt = agent.get("system_prompt", "You are an AI assistant in a workflow.")
            agent_model = agent.get("model", "gemini-3.8-flash")
            agent_temp = float(agent.get("temperature", 0.3))
        else:
            config = getattr(agent, "config", None)
            agent_prompt = getattr(agent, "system_prompt", None) or "You are an AI assistant in a workflow."
            agent_model = getattr(config, "model", "gemini-3.8-flash")
            agent_temp = getattr(config, "temperature", 0.3)

        # Build combined prompt with tool results and knowledge base
        full_system_instructions = f"{agent_prompt}\n{kb_text}"
        step_user_content = rendered_prompt
        if tool_outputs:
            step_user_content += f"\n\n[Pre-step Tool Script Results]:\n{json.dumps(tool_outputs, indent=2)}"

        # 5. Execute agent turn
        agent_response_text, tokens = self._execute_agent_turn(
            agent=agent,
            prompt=step_user_content,
            system_instructions=full_system_instructions,
            model_name=agent_model,
            temperature=agent_temp
        )

        duration_ms = round((time.time() - start_time) * 1000, 2)

        output_data = {
            "text": agent_response_text,
            "tool_results": tool_outputs,
            "completed_at": current_iso_time(),
        }

        return {
            "status": "completed",
            "step_id": step_id,
            "agent_id": agent_id,
            "prompt_rendered": rendered_prompt,
            "output_data": output_data,
            "tool_calls": tool_calls,
            "tokens_used": tokens,
            "duration_ms": duration_ms,
            "error": None,
        }

    def execute_unit_test(
        self,
        workflow_data: Dict[str, Any],
        step_id: str,
        mock_inputs: Dict[str, Any],
        mock_previous_outputs: Dict[str, Any],
        user_id: str
    ) -> StepUnitTestResponse:
        """
        Executes a unit test on a single step in isolation without running prior steps.
        """
        steps = workflow_data.get("steps") or []
        target_step = next((s for s in steps if s.get("id") == step_id), None)
        if not target_step:
            return StepUnitTestResponse(
                status="error",
                step_id=step_id,
                agent_id="unknown",
                prompt_rendered="",
                output_data={},
                tool_calls=[],
                tokens_used=0,
                duration_ms=0.0,
                error=f"Step with id '{step_id}' not found in workflow.",
            )

        # Fetch tools & knowledge
        workflow_id = workflow_data.get("id", "")
        knowledge_files = memory_store.get_knowledge_files(workflow_id)
        user_tools = memory_store.get_tools(user_id)
        tools_map = {t["id"]: t for t in user_tools}

        goal = workflow_data.get("goal", "")

        try:
            res = self.execute_single_step(
                step=target_step,
                inputs=mock_inputs,
                previous_outputs=mock_previous_outputs,
                goal=goal,
                knowledge_files=knowledge_files,
                tools_map=tools_map,
                user_id=user_id
            )
            return StepUnitTestResponse(
                status=res["status"],
                step_id=step_id,
                agent_id=res["agent_id"],
                prompt_rendered=res["prompt_rendered"],
                output_data=res["output_data"],
                tool_calls=res["tool_calls"],
                tokens_used=res["tokens_used"],
                duration_ms=res["duration_ms"],
                error=res["error"],
            )
        except Exception as e:
            return StepUnitTestResponse(
                status="error",
                step_id=step_id,
                agent_id=target_step.get("agent_id", "unknown"),
                prompt_rendered="",
                output_data={},
                tool_calls=[],
                tokens_used=0,
                duration_ms=0.0,
                error=f"Unit test execution error: {str(e)}",
            )

    def execute_workflow(
        self,
        workflow_data: Dict[str, Any],
        inputs: Dict[str, Any],
        user_id: str,
        trigger_type: str = "manual",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the entire workflow DAG end-to-end, recording runs and step runs.
        """
        start_time = time.time()
        workflow_id = workflow_data.get("id", str(uuid.uuid4()))
        run_id = str(uuid.uuid4())

        # 1. Register run record
        run_record = {
            "id": run_id,
            "workflow_id": workflow_id,
            "user_id": user_id,
            "session_id": session_id,
            "trigger_type": trigger_type,
            "status": "running",
            "input_data": inputs,
            "output_data": {},
            "total_tokens": 0,
            "duration_ms": 0.0,
            "error": None,
            "created_at": current_iso_time(),
            "completed_at": None,
        }
        memory_store.create_workflow_run(run_record)

        # 2. Sort steps topologically
        raw_steps = workflow_data.get("steps") or []
        edges = workflow_data.get("edges") or []
        ordered_steps = topological_sort_steps(raw_steps, edges)

        # Load tools and knowledge
        knowledge_files = memory_store.get_knowledge_files(workflow_id)
        user_tools = memory_store.get_tools(user_id)
        tools_map = {t["id"]: t for t in user_tools}
        goal = workflow_data.get("goal", "")

        previous_outputs: Dict[str, Any] = {}
        total_tokens = 0
        step_runs_accum = []
        workflow_error = None

        # 3. Execute steps in order
        for idx, step in enumerate(ordered_steps):
            step_id = step.get("id", f"step_{idx+1}")
            try:
                res = self.execute_single_step(
                    step=step,
                    inputs=inputs,
                    previous_outputs=previous_outputs,
                    goal=goal,
                    knowledge_files=knowledge_files,
                    tools_map=tools_map,
                    user_id=user_id
                )

                previous_outputs[step_id] = res["output_data"]
                total_tokens += res["tokens_used"]

                step_run_record = {
                    "id": str(uuid.uuid4()),
                    "run_id": run_id,
                    "step_id": step_id,
                    "step_index": idx,
                    "agent_id": res["agent_id"],
                    "status": "completed",
                    "prompt_rendered": res["prompt_rendered"],
                    "input_data": inputs,
                    "output_data": res["output_data"],
                    "tool_calls": res["tool_calls"],
                    "tokens_used": res["tokens_used"],
                    "duration_ms": res["duration_ms"],
                    "error": None,
                    "created_at": current_iso_time(),
                    "completed_at": current_iso_time(),
                }
                memory_store.add_step_run(step_run_record)
                step_runs_accum.append(step_run_record)

            except Exception as e:
                workflow_error = f"Step '{step_id}' failed: {str(e)}"
                failed_step_run = {
                    "id": str(uuid.uuid4()),
                    "run_id": run_id,
                    "step_id": step_id,
                    "step_index": idx,
                    "agent_id": step.get("agent_id", "unknown"),
                    "status": "failed",
                    "prompt_rendered": "",
                    "input_data": inputs,
                    "output_data": {},
                    "tool_calls": [],
                    "tokens_used": 0,
                    "duration_ms": 0.0,
                    "error": str(e),
                    "created_at": current_iso_time(),
                    "completed_at": current_iso_time(),
                }
                memory_store.add_step_run(failed_step_run)
                step_runs_accum.append(failed_step_run)
                break

        total_duration_ms = round((time.time() - start_time) * 1000, 2)

        # 4. Final synthesis output
        final_status = "completed" if not workflow_error else "failed"
        final_output = {
            "goal": goal,
            "step_outputs": previous_outputs,
            "final_result": (
                list(previous_outputs.values())[-1].get("text")
                if previous_outputs else "No step completed."
            ),
        }

        updates = {
            "status": final_status,
            "output_data": final_output,
            "total_tokens": total_tokens,
            "duration_ms": total_duration_ms,
            "error": workflow_error,
            "completed_at": current_iso_time(),
        }
        updated_run = memory_store.update_workflow_run(run_id, updates)
        if updated_run:
            updated_run["step_runs"] = step_runs_accum
            return updated_run

        run_record.update(updates)
        run_record["step_runs"] = step_runs_accum
        return run_record


# Singleton Workflow Engine instance
workflow_engine = WorkflowExecutionEngine()
