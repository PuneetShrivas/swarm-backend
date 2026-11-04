"""
Telemetry, Metrics, and Token Consumption Tracker for Azure AI Foundry Pipeline.
"""

import time
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class StepTelemetry:
    """Metrics for a single agent turn in the Azure AI Foundry pipeline."""
    agent_name: str
    role_title: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    conversation_id: str = ""
    response_id: str = ""
    model: Optional[str] = None
    status: str = "completed"
    output_length_chars: int = 0
    preview_snippet: str = ""

    def complete(
        self,
        output_text: str,
        conversation_id: str,
        response_id: str,
        usage: Optional[Any] = None,
        model: Optional[str] = None,
        status: str = "completed",
    ) -> None:
        """Completes the step and records execution timings and token usage."""
        self.end_time = time.perf_counter()
        self.duration_seconds = round(self.end_time - self.start_time, 3)
        self.conversation_id = str(conversation_id or "")
        self.response_id = str(response_id or "")
        self.model = str(model) if model else None
        self.status = str(status or "completed")
        self.output_length_chars = len(output_text or "")
        clean_text = " ".join((output_text or "").split())
        self.preview_snippet = clean_text[:120] + ("..." if len(clean_text) > 120 else "")

        if usage:
            self.input_tokens = getattr(usage, "input_tokens", 0) or 0
            self.output_tokens = getattr(usage, "output_tokens", 0) or 0
            self.total_tokens = getattr(usage, "total_tokens", 0) or (self.input_tokens + self.output_tokens)


@dataclass
class PipelineTelemetry:
    """End-to-end execution metrics across all pipeline steps."""
    user_prompt: str = ""
    started_at_iso: str = ""
    completed_at_iso: str = ""
    total_duration_seconds: float = 0.0
    steps: List[StepTelemetry] = field(default_factory=list)
    output_files: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_input_tokens(self) -> int:
        return sum(s.input_tokens for s in self.steps)

    @property
    def total_output_tokens(self) -> int:
        return sum(s.output_tokens for s in self.steps)

    @property
    def total_tokens(self) -> int:
        return sum(s.total_tokens for s in self.steps)

    def to_dict(self) -> Dict[str, Any]:
        """Converts telemetry to a JSON-serializable dictionary."""
        return {
            "user_prompt": self.user_prompt,
            "started_at": self.started_at_iso,
            "completed_at": self.completed_at_iso,
            "total_duration_seconds": self.total_duration_seconds,
            "total_tokens": {
                "input": self.total_input_tokens,
                "output": self.total_output_tokens,
                "total": self.total_tokens,
            },
            "steps": [asdict(s) for s in self.steps],
            "output_files": self.output_files,
            "metadata": self.metadata,
        }

    def format_console_summary(self) -> str:
        """Formats an executive summary table for terminal display."""
        lines = [
            "",
            "=" * 90,
            "             AZURE FOUNDRY AGENT TRIO PIPELINE EXECUTION SUMMARY",
            "=" * 90,
            f" Started At:        {self.started_at_iso}",
            f" Completed At:      {self.completed_at_iso}",
            f" Total Duration:    {self.total_duration_seconds:.2f} seconds",
            f" Total Tokens:      {self.total_tokens:,} (Input: {self.total_input_tokens:,} | Output: {self.total_output_tokens:,})",
            "-" * 90,
            f" {'#':<3} | {'Agent / Step':<22} | {'Time (s)':<9} | {'Input Tok':<10} | {'Output Tok':<10} | {'Total Tok':<10} | {'Status'}",
            "-" * 90,
        ]

        for i, s in enumerate(self.steps, 1):
            agent_label = f"{s.agent_name} ({s.role_title})"
            if len(agent_label) > 22:
                agent_label = agent_label[:19] + "..."
            lines.append(
                f" {i:<3} | {agent_label:<22} | {s.duration_seconds:<9.2f} | "
                f"{s.input_tokens:<10,d} | {s.output_tokens:<10,d} | {s.total_tokens:<10,d} | {s.status}"
            )

        lines.extend([
            "=" * 90,
            " GENERATED ARTIFACTS:",
        ])
        if self.output_files:
            for kind, path in self.output_files.items():
                lines.append(f"  * {kind.upper():<16}: {path}")
        else:
            lines.append("  * (No output artifacts registered)")

        lines.append("=" * 90)
        lines.append("")
        return "\n".join(lines)

    def format_fast_comparison_summary(self) -> str:
        """Formats a comparative summary table specifically for the fast alternative pipeline."""
        lines = [
            "",
            "=" * 92,
            "         AZURE FOUNDRY FAST ALTERNATIVE PIPELINE (COMPARISON SUMMARY)",
            "=" * 92,
            f" Started At:        {self.started_at_iso}",
            f" Completed At:      {self.completed_at_iso}",
            f" Total Duration:    {self.total_duration_seconds:.2f} seconds",
            f" Total Tokens:      {self.total_tokens:,} (Input: {self.total_input_tokens:,} | Output: {self.total_output_tokens:,})",
            "-" * 92,
            f" {'#':<3} | {'Execution Step':<28} | {'Duration':<10} | {'Input Tok':<10} | {'Output Tok':<10} | {'Total Tok':<10} | {'Status'}",
            "-" * 92,
        ]

        agent_step: Optional[StepTelemetry] = None
        direct_step: Optional[StepTelemetry] = None

        for i, s in enumerate(self.steps, 1):
            if "report-generator" in s.agent_name.lower():
                agent_step = s
            elif "model" in s.agent_name.lower() or "direct" in s.role_title.lower() or "claude" in s.agent_name.lower():
                direct_step = s

            label = f"{s.agent_name} ({s.role_title})"
            if len(label) > 28:
                label = label[:25] + "..."
            lines.append(
                f" {i:<3} | {label:<28} | {s.duration_seconds:<9.2f}s | "
                f"{s.input_tokens:<10,d} | {s.output_tokens:<10,d} | {s.total_tokens:<10,d} | {s.status}"
            )

        if agent_step and direct_step:
            lines.extend([
                "-" * 92,
                " GENERATION PATHWAY COMPARISON:",
                f"  * Pathway 1 (Agent: {agent_step.agent_name}):   {agent_step.duration_seconds:.2f}s  |  {agent_step.total_tokens:,} tokens",
                f"  * Pathway 2 (Direct: {direct_step.agent_name}):  {direct_step.duration_seconds:.2f}s  |  {direct_step.total_tokens:,} tokens",
            ])
            if agent_step.duration_seconds > 0 and direct_step.duration_seconds > 0:
                diff_sec = agent_step.duration_seconds - direct_step.duration_seconds
                if diff_sec > 0:
                    pct = (diff_sec / agent_step.duration_seconds) * 100
                    lines.append(f"  → Direct Model was {abs(diff_sec):.2f}s faster ({pct:.1f}% latency reduction) than Agent Generator.")
                elif diff_sec < 0:
                    pct = (abs(diff_sec) / direct_step.duration_seconds) * 100
                    lines.append(f"  → Agent Generator was {abs(diff_sec):.2f}s faster ({pct:.1f}% latency reduction) than Direct Model.")

        lines.extend([
            "=" * 92,
            " GENERATED ARTIFACTS:",
        ])
        if self.output_files:
            for kind, path in self.output_files.items():
                lines.append(f"  * {kind.upper():<20}: {path}")
        else:
            lines.append("  * (No output artifacts registered)")

        lines.append("=" * 92)
        lines.append("")
        return "\n".join(lines)
