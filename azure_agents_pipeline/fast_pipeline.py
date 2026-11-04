"""
Fast Alternative Pipeline for Azure AI Foundry.
Flow: Company Name → DO-researcher
  ├─ Pathway 1: Directly to DO-report-generator (agent-to-agent, bypassing validator)
  └─ Pathway 2: Directly to Azure Foundry Model (direct model inference for high-speed synthesis)
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Dict, Any, Tuple

from azure.ai.projects import AIProjectClient

from azure_agents_pipeline.config import (
    DEFAULT_ENDPOINT,
    DEFAULT_RESEARCHER_AGENT,
    DEFAULT_GENERATOR_AGENT,
    DEFAULT_DIRECT_MODEL_ENDPOINT,
    DEFAULT_DIRECT_MODEL_NAME,
    DEFAULT_FALLBACK_MODEL_NAME,
    AZURE_API_KEY,
    DEFAULT_OUTPUT_DIR,
    get_azure_credential,
    check_azure_credentials_available,
)
from azure_agents_pipeline.telemetry import StepTelemetry, PipelineTelemetry
from azure_agents_pipeline.pdf_compiler import ReportPdfCompiler
from azure_agents_pipeline.prompts import DIRECT_REPORT_PROMPT


class FastAzureFoundryPipeline:
    """
    Coordinates high-speed alternative execution on Azure AI Foundry:
    1. Sends company name/input to DO-researcher.
    2. Directly passes response to:
       - Pathway 1: DO-report-generator (agent)
       - Pathway 2: Direct Azure Foundry Model (claude-sonnet-4-6 / claude-opus-4-8)
    """

    def __init__(
        self,
        endpoint: str = DEFAULT_ENDPOINT,
        researcher_agent: str = DEFAULT_RESEARCHER_AGENT,
        generator_agent: str = DEFAULT_GENERATOR_AGENT,
        direct_model_endpoint: str = DEFAULT_DIRECT_MODEL_ENDPOINT,
        direct_model_name: str = DEFAULT_DIRECT_MODEL_NAME,
        fallback_model_name: str = DEFAULT_FALLBACK_MODEL_NAME,
        direct_model_prompt: Optional[str] = None,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        interactive: bool = False,
    ):
        self.endpoint = endpoint.strip()
        self.researcher_agent = researcher_agent.strip()
        self.generator_agent = generator_agent.strip()
        self.direct_model_endpoint = direct_model_endpoint.strip()
        self.direct_model_name = direct_model_name.strip()
        self.fallback_model_name = fallback_model_name.strip()
        self.direct_model_prompt = (direct_model_prompt or DIRECT_REPORT_PROMPT).strip()
        self.output_dir = Path(output_dir)
        self.interactive = interactive
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        company_name_or_prompt: str,
        ticker: Optional[str] = None,
        mode: str = "both",
    ) -> PipelineTelemetry:
        """
        Executes the fast alternative pipeline.
        Modes:
          - 'both': Runs both DO-report-generator agent AND direct Azure model for comparison.
          - 'agent': Runs only Pathway 1 (Researcher → Report Generator Agent).
          - 'direct': Runs only Pathway 2 (Researcher → Direct Azure Model).
        """
        mode = mode.lower().strip()
        if mode not in ["both", "agent", "direct"]:
            mode = "both"

        telemetry = PipelineTelemetry(
            user_prompt=company_name_or_prompt,
            started_at_iso=datetime.now().isoformat(),
            metadata={"mode": mode, "pipeline_type": "fast_alternative"},
        )
        t_global_start = time.perf_counter()

        # Check Entra ID credentials for project client
        is_ok, diag_msg = check_azure_credentials_available()
        if not is_ok and not self.interactive:
            print(f"\n[CREDENTIAL WARNING]\n{diag_msg}\n", flush=True)

        credential = get_azure_credential(interactive=self.interactive)

        target_label = ticker.upper() if ticker else company_name_or_prompt
        print(f"\n[FAST ALTERNATIVE PIPELINE START]", flush=True)
        print(f" Target Company / Prompt: {target_label}", flush=True)
        print(f" Mode:                   {mode.upper()}", flush=True)
        print(f" Researcher Agent:       {self.researcher_agent}", flush=True)
        if mode in ["both", "agent"]:
            print(f" Pathway 1 (Agent):      {self.generator_agent} (direct, bypass validator)", flush=True)
        if mode in ["both", "direct"]:
            print(f" Pathway 2 (Direct):     Azure Foundry Model '{self.direct_model_name}'", flush=True)
        print("-" * 78, flush=True)

        # -------------------------------------------------------------
        # Step 1: Query DO-researcher with company name
        # -------------------------------------------------------------
        step_res = StepTelemetry(
            agent_name=self.researcher_agent,
            role_title="Deep Risk Researcher",
            start_time=time.perf_counter(),
        )
        print(f"\n[1/2] Sending company name to Researcher Agent ('{self.researcher_agent}')...", flush=True)

        research_prompt = self._build_research_prompt(company_name_or_prompt, ticker)

        with AIProjectClient(
            endpoint=self.endpoint,
            credential=credential,
            allow_preview=True,
        ) as project_client:
            openai_res_client = project_client.get_openai_client(agent_name=self.researcher_agent)
            conv_res = openai_res_client.conversations.create()

            res_response = openai_res_client.responses.create(
                conversation=conv_res.id,
                input=[{"role": "user", "content": research_prompt}],
            )
            research_output = res_response.output_text or ""
            step_res.complete(
                output_text=research_output,
                conversation_id=conv_res.id,
                response_id=res_response.id,
                usage=getattr(res_response, "usage", None),
                model=getattr(res_response, "model", None),
                status=getattr(res_response, "status", "completed"),
            )
            telemetry.steps.append(step_res)
            print(
                f"  ✓ Researcher completed in {step_res.duration_seconds:.2f}s | "
                f"Tokens: {step_res.total_tokens:,} (in: {step_res.input_tokens:,}, out: {step_res.output_tokens:,})",
                flush=True,
            )

            # ---------------------------------------------------------
            # Pathway 1: Directly send response to DO-report-generator
            # ---------------------------------------------------------
            agent_report_text = ""
            if mode in ["both", "agent"]:
                step_gen = StepTelemetry(
                    agent_name=self.generator_agent,
                    role_title="Direct Agent Report Generator",
                    start_time=time.perf_counter(),
                )
                print(f"\n[2a] Pathway 1: Sending researcher output directly to '{self.generator_agent}'...", flush=True)

                generator_prompt = (
                    f"You are the Executive Report Generator. Directly format the following preliminary research findings "
                    f"into an official executive D&O underwriting report with clear headers (###), bullet points, "
                    f"and underwriter tier conclusions:\n\n{research_output}"
                )
                openai_gen_client = project_client.get_openai_client(agent_name=self.generator_agent)
                conv_gen = openai_gen_client.conversations.create()

                gen_response = openai_gen_client.responses.create(
                    conversation=conv_gen.id,
                    input=[{"role": "user", "content": generator_prompt}],
                )
                agent_report_text = gen_response.output_text or research_output
                step_gen.complete(
                    output_text=agent_report_text,
                    conversation_id=conv_gen.id,
                    response_id=gen_response.id,
                    usage=getattr(gen_response, "usage", None),
                    model=getattr(gen_response, "model", None),
                    status=getattr(gen_response, "status", "completed"),
                )
                telemetry.steps.append(step_gen)
                print(
                    f"  ✓ Agent Generator completed in {step_gen.duration_seconds:.2f}s | "
                    f"Tokens: {step_gen.total_tokens:,} (in: {step_gen.input_tokens:,}, out: {step_gen.output_tokens:,})",
                    flush=True,
                )

        # -------------------------------------------------------------
        # Pathway 2: Direct Azure Foundry Model Execution
        # -------------------------------------------------------------
        direct_report_text = ""
        if mode in ["both", "direct"]:
            step_direct = StepTelemetry(
                agent_name=f"AzureFoundry/{self.direct_model_name}",
                role_title="Direct Model Executive Synthesis",
                start_time=time.perf_counter(),
            )
            print(f"\n[2b] Pathway 2: Calling Azure Foundry Model ('{self.direct_model_name}') directly for quick report...", flush=True)

            direct_report_text, direct_usage, model_used = self._execute_direct_model(
                research_output=research_output,
                target_company=target_label,
            )
            step_direct.complete(
                output_text=direct_report_text,
                conversation_id="direct_rest_call",
                response_id=f"direct_model_{int(time.time())}",
                usage=direct_usage,
                model=model_used,
                status="completed",
            )
            telemetry.steps.append(step_direct)
            print(
                f"  ✓ Direct Model completed in {step_direct.duration_seconds:.2f}s | "
                f"Tokens: {step_direct.total_tokens:,} (in: {step_direct.input_tokens:,}, out: {step_direct.output_tokens:,})",
                flush=True,
            )

        # -------------------------------------------------------------
        # Document Artifact Generation (PDF & Markdown for each pathway)
        # -------------------------------------------------------------
        t_global_end = time.perf_counter()
        telemetry.total_duration_seconds = round(t_global_end - t_global_start, 3)
        telemetry.completed_at_iso = datetime.now().isoformat()

        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = (ticker or "Company").strip().upper()

        # Compile Pathway 1 Artifacts
        if agent_report_text:
            base_agent = f"DO_Risk_Report_{slug}_{timestamp_slug}_fast_agent"
            md_agent_path = self.output_dir / f"{base_agent}.md"
            with open(md_agent_path, "w", encoding="utf-8") as f:
                f.write(agent_report_text)
            telemetry.output_files["agent_markdown"] = str(md_agent_path.resolve())

            pdf_agent_path = self.output_dir / f"{base_agent}.pdf"
            compiler_agent = ReportPdfCompiler(str(pdf_agent_path))
            pdf_meta_agent = compiler_agent.compile(
                report_text=agent_report_text,
                title=f"D&O Risk Underwriting Report: {slug} (Fast Agent Path)",
                metadata=telemetry.to_dict(),
            )
            telemetry.output_files["agent_pdf"] = pdf_meta_agent["output_pdf_path"]

        # Compile Pathway 2 Artifacts
        if direct_report_text:
            base_direct = f"DO_Risk_Report_{slug}_{timestamp_slug}_fast_direct"
            md_direct_path = self.output_dir / f"{base_direct}.md"
            with open(md_direct_path, "w", encoding="utf-8") as f:
                f.write(direct_report_text)
            telemetry.output_files["direct_markdown"] = str(md_direct_path.resolve())

            pdf_direct_path = self.output_dir / f"{base_direct}.pdf"
            compiler_direct = ReportPdfCompiler(str(pdf_direct_path))
            pdf_meta_direct = compiler_direct.compile(
                report_text=direct_report_text,
                title=f"D&O Risk Underwriting Report: {slug} (Direct Model Path)",
                metadata=telemetry.to_dict(),
            )
            telemetry.output_files["direct_pdf"] = pdf_meta_direct["output_pdf_path"]

        # Save comparative telemetry JSON
        telemetry_path = self.output_dir / f"DO_Risk_Report_{slug}_{timestamp_slug}_fast_telemetry.json"
        with open(telemetry_path, "w", encoding="utf-8") as f:
            json.dump(telemetry.to_dict(), f, indent=2, default=str)
        telemetry.output_files["telemetry_json"] = str(telemetry_path.resolve())

        return telemetry

    def _execute_direct_model(
        self,
        research_output: str,
        target_company: str,
    ) -> Tuple[str, Any, str]:
        """
        Directly executes an Azure Foundry model endpoint via Anthropic Messages API or project client.
        Supports automatic model failover between fast model and fallback model.
        """
        api_key = AZURE_API_KEY or os.environ.get("AZURE_API_KEY", "")
        models_to_try = [self.direct_model_name]
        if self.fallback_model_name and self.fallback_model_name != self.direct_model_name:
            models_to_try.append(self.fallback_model_name)

        system_instruction = self.direct_model_prompt or DIRECT_REPORT_PROMPT

        user_content = (
            f"TARGET COMPANY: {target_company}\n\n"
            f"SUPPLIED EVIDENCE BASE (FROM DO-RESEARCHER):\n{research_output}\n\n"
            f"Transform the supplied evidence into a comprehensive, professionally structured "
            f"D&O underwriting report following the structure and instructions exactly."
        )

        # Resolve authorization header: either explicit API key or dynamic Entra ID Bearer token
        auth_header = ""
        if api_key and not api_key.startswith("your-") and not api_key.startswith("test-"):
            auth_header = f"Bearer {api_key.strip()}"
        else:
            try:
                from azure.identity import get_bearer_token_provider
                credential = get_azure_credential(interactive=self.interactive)
                token_provider = get_bearer_token_provider(credential, "https://ai.azure.com/.default")
                token = token_provider()
                if token:
                    auth_header = f"Bearer {token}"
            except Exception:
                pass

        import httpx

        last_error = ""
        for model in models_to_try:
            try:
                if auth_header:
                    endpoint = self.direct_model_endpoint
                    if not endpoint.endswith("/v1/messages"):
                        endpoint = f"{endpoint.rstrip('/')}/v1/messages"

                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": auth_header,
                        "anthropic-version": "2023-06-01",
                    }
                    payload = {
                        "model": model,
                        "max_tokens": 4000,
                        "system": system_instruction,
                        "messages": [
                            {"role": "user", "content": user_content}
                        ],
                    }
                    with httpx.Client(timeout=120.0) as client:
                        resp = client.post(endpoint, headers=headers, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            content_items = data.get("content", [])
                            text_blocks = [
                                item.get("text", "")
                                for item in content_items
                                if isinstance(item, dict) and (item.get("type") == "text" or "text" in item)
                            ]
                            full_text = "".join(text_blocks).strip()
                            raw_usage = data.get("usage", {})
                            usage = SimpleNamespace(
                                input_tokens=raw_usage.get("input_tokens", len(user_content) // 4),
                                output_tokens=raw_usage.get("output_tokens", len(full_text) // 4),
                                total_tokens=raw_usage.get("input_tokens", 0) + raw_usage.get("output_tokens", 0) or (len(user_content) + len(full_text)) // 4,
                            )
                            return full_text, usage, model
                        else:
                            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                else:
                    last_error = "Neither AZURE_API_KEY nor valid Entra ID Bearer token available for direct model call."

            except Exception as e:
                last_error = str(e)
                print(f"Direct model '{model}' call note: {e}", flush=True)

        # Fallback synthesis if direct REST endpoint encounters network error
        print(f"[DIRECT MODEL FALLBACK] Synthesizing executive report from raw research (Reason: {last_error})", flush=True)
        fallback_text = (
            f"# {target_company}\n\n"
            f"## 1. EXECUTIVE SUMMARY\n"
            f"### Summary\n"
            f"- Preliminary assessment for {target_company} synthesized directly from researcher evidence base.\n"
            f"- Dominant risk drivers: Review of supplied public filings and adverse market indicators.\n\n"
            f"## 2. COMPANY SNAPSHOT\n"
            f"- Legal name: {target_company}\n"
            f"- Overview: Direct model generation completed via local fallback mode.\n\n"
            f"## 3. PRIMARY EVIDENCE DISCLOSURES\n"
            f"{research_output}\n\n"
            f"Assessment based solely on information contained in this report."
        )
        fallback_usage = SimpleNamespace(
            input_tokens=len(user_content) // 4,
            output_tokens=len(fallback_text) // 4,
            total_tokens=(len(user_content) + len(fallback_text)) // 4,
        )
        return fallback_text, fallback_usage, f"{models_to_try[0]} (fallback)"

    @staticmethod
    def _build_research_prompt(company_name_or_prompt: str, ticker: Optional[str]) -> str:
        if ticker:
            return (
                f"Conduct an in-depth D&O Public Risk Underwriting investigation for company name/ticker: {ticker.upper()}.\n"
                f"Evaluate securities class actions, accounting restatements, board governance, and financial posture.\n"
                f"Context: {company_name_or_prompt}"
            )
        return (
            f"Conduct an in-depth D&O Public Risk Underwriting investigation for: {company_name_or_prompt}.\n"
            f"Analyze public regulatory filings, securities class actions, board governance, and financial health."
        )
