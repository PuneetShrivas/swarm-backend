"""
Azure AI Foundry Three-Agent Pipeline (DO-researcher → DO-validator → DO-report-generator).
"""

from azure_agents_pipeline.config import (
    DEFAULT_ENDPOINT,
    DEFAULT_RESEARCHER_AGENT,
    DEFAULT_VALIDATOR_AGENT,
    DEFAULT_GENERATOR_AGENT,
    DEFAULT_DIRECT_MODEL_ENDPOINT,
    DEFAULT_DIRECT_MODEL_NAME,
    DEFAULT_FALLBACK_MODEL_NAME,
    DEFAULT_OUTPUT_DIR,
)
from azure_agents_pipeline.telemetry import StepTelemetry, PipelineTelemetry
from azure_agents_pipeline.pdf_compiler import ReportPdfCompiler
from azure_agents_pipeline.pipeline import AzureFoundryAgentTrioPipeline
from azure_agents_pipeline.fast_pipeline import FastAzureFoundryPipeline

__all__ = [
    "DEFAULT_ENDPOINT",
    "DEFAULT_RESEARCHER_AGENT",
    "DEFAULT_VALIDATOR_AGENT",
    "DEFAULT_GENERATOR_AGENT",
    "DEFAULT_DIRECT_MODEL_ENDPOINT",
    "DEFAULT_DIRECT_MODEL_NAME",
    "DEFAULT_FALLBACK_MODEL_NAME",
    "DEFAULT_OUTPUT_DIR",
    "StepTelemetry",
    "PipelineTelemetry",
    "ReportPdfCompiler",
    "AzureFoundryAgentTrioPipeline",
    "FastAzureFoundryPipeline",
]
