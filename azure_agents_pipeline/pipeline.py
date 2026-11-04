"""
Sequential Coordinator for Azure AI Foundry Three-Agent Pipeline.
Orchestrates: DO-researcher → DO-validator → DO-report-generator.
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from azure.ai.projects import AIProjectClient

from azure_agents_pipeline.config import (
    DEFAULT_ENDPOINT,
    DEFAULT_RESEARCHER_AGENT,
    DEFAULT_VALIDATOR_AGENT,
    DEFAULT_GENERATOR_AGENT,
    DEFAULT_OUTPUT_DIR,
    get_azure_credential,
    check_azure_credentials_available,
)
from azure_agents_pipeline.telemetry import StepTelemetry, PipelineTelemetry
from azure_agents_pipeline.pdf_compiler import ReportPdfCompiler


class AzureFoundryAgentTrioPipeline:
    """
    Coordinates execution of three preview agents deployed in Azure AI Foundry:
    1. DO-researcher: Ingests user input/ticker, researches risk signals, drafts preliminary report.
    2. DO-validator: Audits the draft against underwriting guidelines, removes contradictions, validates.
    3. DO-report-generator: Formats the finalized report into publication-ready executive structure.
    Finally compiles a PDF artifact and records end-to-end telemetry.
    """

    def __init__(
        self,
        endpoint: str = DEFAULT_ENDPOINT,
        researcher_agent: str = DEFAULT_RESEARCHER_AGENT,
        validator_agent: str = DEFAULT_VALIDATOR_AGENT,
        generator_agent: str = DEFAULT_GENERATOR_AGENT,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        interactive: bool = False,
    ):
        self.endpoint = endpoint.strip()
        self.researcher_agent = researcher_agent.strip()
        self.validator_agent = validator_agent.strip()
        self.generator_agent = generator_agent.strip()
        self.output_dir = Path(output_dir)
        self.interactive = interactive
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, user_input: str, ticker: Optional[str] = None) -> PipelineTelemetry:
        """
        Executes the 3-agent chain synchronously, tracking duration, token counts, and file artifacts.
        """
        telemetry = PipelineTelemetry(
            user_prompt=user_input,
            started_at_iso=datetime.now().isoformat(),
        )
        t_global_start = time.perf_counter()

        # Verify credentials before establishing connection
        is_ok, diag_msg = check_azure_credentials_available()
        if not is_ok and not self.interactive:
            print(f"\n[CREDENTIAL WARNING]\n{diag_msg}\n", flush=True)

        credential = get_azure_credential(interactive=self.interactive)

        print(f"\n[AZURE FOUNDRY PIPELINE START]", flush=True)
        print(f" Endpoint:           {self.endpoint}", flush=True)
        print(f" Target Public Entity: {ticker or 'Custom Request'}", flush=True)
        print(f" Agents:             {self.researcher_agent} → {self.validator_agent} → {self.generator_agent}", flush=True)
        print(f" Output Directory:   {self.output_dir.resolve()}", flush=True)
        print("-" * 75, flush=True)

        with AIProjectClient(
            endpoint=self.endpoint,
            credential=credential,
            allow_preview=True,
        ) as project_client:

            # ---------------------------------------------------------
            # Step 1: DO-researcher
            # ---------------------------------------------------------
            step1 = StepTelemetry(
                agent_name=self.researcher_agent,
                role_title="Deep Risk Researcher",
                start_time=time.perf_counter(),
            )
            print(f"\n[1/3] Calling Researcher Agent ('{self.researcher_agent}')...", flush=True)

            researcher_prompt = self._build_researcher_prompt(user_input, ticker)
            openai_res_client = project_client.get_openai_client(agent_name=self.researcher_agent)
            conv_res = openai_res_client.conversations.create()

            res_response = openai_res_client.responses.create(
                conversation=conv_res.id,
                input=[{"role": "user", "content": researcher_prompt}],
            )
            research_draft = res_response.output_text or ""
            step1.complete(
                output_text=research_draft,
                conversation_id=conv_res.id,
                response_id=res_response.id,
                usage=getattr(res_response, "usage", None),
                model=getattr(res_response, "model", None),
                status=getattr(res_response, "status", "completed"),
            )
            telemetry.steps.append(step1)
            print(
                f"  ✓ Researcher completed in {step1.duration_seconds:.2f}s | "
                f"Tokens: {step1.total_tokens:,} (in: {step1.input_tokens:,}, out: {step1.output_tokens:,})",
                flush=True,
            )

            # ---------------------------------------------------------
            # Step 2: DO-validator
            # ---------------------------------------------------------
            step2 = StepTelemetry(
                agent_name=self.validator_agent,
                role_title="Adversarial Audit & Validator",
                start_time=time.perf_counter(),
            )
            print(f"\n[2/3] Calling Validator Agent ('{self.validator_agent}')...", flush=True)

            validator_prompt = self._build_validator_prompt(research_draft, ticker)
            openai_val_client = project_client.get_openai_client(agent_name=self.validator_agent)
            conv_val = openai_val_client.conversations.create()

            val_response = openai_val_client.responses.create(
                conversation=conv_val.id,
                input=[{"role": "user", "content": validator_prompt}],
            )
            validated_draft = val_response.output_text or ""
            step2.complete(
                output_text=validated_draft,
                conversation_id=conv_val.id,
                response_id=val_response.id,
                usage=getattr(val_response, "usage", None),
                model=getattr(val_response, "model", None),
                status=getattr(val_response, "status", "completed"),
            )
            telemetry.steps.append(step2)
            print(
                f"  ✓ Validator completed in {step2.duration_seconds:.2f}s | "
                f"Tokens: {step2.total_tokens:,} (in: {step2.input_tokens:,}, out: {step2.output_tokens:,})",
                flush=True,
            )

            # ---------------------------------------------------------
            # Step 3: DO-report-generator
            # ---------------------------------------------------------
            step3 = StepTelemetry(
                agent_name=self.generator_agent,
                role_title="Executive Report Formatter",
                start_time=time.perf_counter(),
            )
            print(f"\n[3/3] Calling Report Generator Agent ('{self.generator_agent}')...", flush=True)

            generator_prompt = self._build_generator_prompt(validated_draft, ticker)
            openai_gen_client = project_client.get_openai_client(agent_name=self.generator_agent)
            conv_gen = openai_gen_client.conversations.create()

            gen_response = openai_gen_client.responses.create(
                conversation=conv_gen.id,
                input=[{"role": "user", "content": generator_prompt}],
            )
            final_report_text = gen_response.output_text or validated_draft
            step3.complete(
                output_text=final_report_text,
                conversation_id=conv_gen.id,
                response_id=gen_response.id,
                usage=getattr(gen_response, "usage", None),
                model=getattr(gen_response, "model", None),
                status=getattr(gen_response, "status", "completed"),
            )
            telemetry.steps.append(step3)
            print(
                f"  ✓ Generator completed in {step3.duration_seconds:.2f}s | "
                f"Tokens: {step3.total_tokens:,} (in: {step3.input_tokens:,}, out: {step3.output_tokens:,})",
                flush=True,
            )

        # ---------------------------------------------------------
        # Finalization & Document Artifact Generation
        # ---------------------------------------------------------
        t_global_end = time.perf_counter()
        telemetry.total_duration_seconds = round(t_global_end - t_global_start, 3)
        telemetry.completed_at_iso = datetime.now().isoformat()

        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_slug = (ticker or "Report").strip().upper()
        base_name = f"DO_Risk_Report_{target_slug}_{timestamp_slug}"

        # 1. Save Markdown Raw Artifact
        md_path = self.output_dir / f"{base_name}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(final_report_text)
        telemetry.output_files["markdown"] = str(md_path.resolve())

        # 2. Compile Publication-Grade PDF Artifact
        pdf_path = self.output_dir / f"{base_name}.pdf"
        compiler = ReportPdfCompiler(str(pdf_path))
        pdf_meta = compiler.compile(
            report_text=final_report_text,
            title=f"D&O Risk Underwriting Assessment: {target_slug}",
            metadata=telemetry.to_dict(),
        )
        telemetry.output_files["pdf"] = pdf_meta["output_pdf_path"]
        telemetry.metadata["pdf_file_size_bytes"] = pdf_meta["file_size_bytes"]
        telemetry.metadata["pdf_sha256"] = pdf_meta["sha256_checksum"]

        # 3. Save Telemetry JSON
        json_path = self.output_dir / f"{base_name}_telemetry.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(telemetry.to_dict(), f, indent=2, default=str)
        telemetry.output_files["telemetry_json"] = str(json_path.resolve())

        return telemetry

    @staticmethod
    def _build_researcher_prompt(user_input: str, ticker: Optional[str]) -> str:
        if ticker:
            return (
                f"Conduct an in-depth D&O Public Risk Underwriting investigation and draft a comprehensive report "
                f"for target company: {ticker.upper()}.\n"
                f"Core areas required:\n"
                f"1. Company Snapshot & Authoritative Auditor\n"
                f"2. Financial Overview & US-GAAP Disclosures\n"
                f"3. Securities Class Action (SCA) Risk & Historical Litigation\n"
                f"4. Regulatory Enforcement & Accounting Scrutiny\n"
                f"5. Board Governance & Key Disclosures\n"
                f"6. D&O Underwriting Verdict & Band Register\n\n"
                f"Additional user instructions:\n{user_input}"
            )
        return user_input

    @staticmethod
    def _build_validator_prompt(research_draft: str, ticker: Optional[str]) -> str:
        entity_hint = f" for {ticker.upper()}" if ticker else ""
        return (
            f"You are the D&O Risk Underwriting Validator. Perform a rigorous adversarial audit "
            f"on the following preliminary research report{entity_hint}.\n\n"
            f"CRITICAL AUDIT RULES:\n"
            f"1. Remove any unsubstantiated claims or speculative extrapolations not supported by primary disclosures.\n"
            f"2. Ensure any news or events outside a 12-month calendar window are explicitly labeled or removed.\n"
            f"3. Ensure D&O risk tiers adhere strictly to: Contained, Elevated, High-Volatility, or Severe Tail Exposure.\n"
            f"4. Eliminate prohibited dollar retention recommendations (e.g. '$25M-$50M retention') and use proper tower attachment framing.\n"
            f"5. Output the finalized, audited report in clean, structured markdown.\n\n"
            f"PRELIMINARY RESEARCH REPORT:\n{research_draft}"
        )

    @staticmethod
    def _build_generator_prompt(validated_draft: str, ticker: Optional[str]) -> str:
        entity_hint = f" for {ticker.upper()}" if ticker else ""
        return (
            f"You are the Executive Report Formatter. Take the following audited risk report{entity_hint} "
            f"and format it into a publication-ready executive D&O underwriting report suitable for PDF rendering.\n"
            f"Preserve all findings, inline citations, section headers (using ###), bullet points, and underwriter conclusions.\n\n"
            f"AUDITED REPORT:\n{validated_draft}"
        )
