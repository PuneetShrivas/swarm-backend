"""
test_pdf_report_artifact.py - Automated test suite for PDF attachment report generation & dual output artifacts.
"""
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_generator import synthesize_on_the_fly_workflow
from app.agents.file_creator.tools import generate_pdf_document
from app.main import extract_file_artifact_from_turn


def test_artifact_report_workflow_synthesis():
    """Verify on-the-fly workflow orchestration produces a 3-agent pipeline for PDF report generation."""
    mock_pdf = {
        "id": "art-pdf-test-1",
        "name": "annual_report.pdf",
        "filename": "annual_report.pdf",
        "type": "pdf",
        "content": "JVBERi0xLjQK...",
    }

    # Test with /artifact template command
    wf_template = synthesize_on_the_fly_workflow(
        prompt="prepare a report according to /artifact [Executive Summary Report]",
        attached_artifacts=[mock_pdf],
    )

    assert wf_template is not None, "Workflow should not be None"
    assert wf_template.get("is_multi_step") is True, "Workflow should be multi-step"
    steps = wf_template.get("steps", [])
    assert len(steps) == 3, f"Expected 3 steps, got {len(steps)}"
    assert steps[0]["agent_id"] == "file_parser", f"Step 1 should be file_parser, got {steps[0]['agent_id']}"
    assert steps[1]["agent_id"] == "writer", f"Step 2 should be writer, got {steps[1]['agent_id']}"
    assert steps[2]["agent_id"] == "synthesizer", f"Step 3 should be synthesizer, got {steps[2]['agent_id']}"
    assert steps[0]["id"] in steps[1]["depends_on"]
    assert steps[1]["id"] in steps[2]["depends_on"]

    # Test with generic report request with attached PDF
    wf_report = synthesize_on_the_fly_workflow(
        prompt="prepare a report from the attached financial statements",
        attached_artifacts=[mock_pdf],
    )
    assert wf_report.get("is_multi_step") is True
    assert wf_report["steps"][0]["agent_id"] == "file_parser"


def test_pdf_document_generator_styling_and_escaping():
    """Verify generate_pdf_document constructs valid base64 PDF and escapes XML special characters."""
    result = generate_pdf_document(
        title="Quarterly Business Review & Financial Outlook <Q4>",
        subtitle="Confidential & Grounded Synthesis",
        sections=[
            {
                "heading": "Executive Summary & Risk Metrics",
                "content": "Revenue grew > 18% YoY with < 5% operating variance & zero security incidents.",
                "bullets": [
                    "Operating cash flow reached $4.2M & exceeded hurdle rate",
                    "Net churn remained < 1.2% across tier-1 enterprises",
                ],
            }
        ],
        tables=[
            {
                "headers": ["Division", "Target ARR", "Actual ARR", "Health"],
                "rows": [
                    ["North America", "$12.0M", "$14.2M", "Strong"],
                    ["EMEA", "$8.0M", "$8.6M", "On Track"],
                ],
            }
        ],
        filename="qbr_review_q4.pdf",
    )

    assert result.get("status") == "created"
    assert result.get("filename") == "qbr_review_q4.pdf"
    assert result.get("mime_type") == "application/pdf"
    assert result.get("is_base64") is True
    assert result.get("downloadable") is True
    assert result.get("size_bytes", 0) > 1000
    assert bool(result.get("content"))


def test_extract_file_artifact_dual_output():
    """Verify turn extraction produces dual markdown output and ready-to-download PDF artifact."""
    mock_pdf = {
        "id": "art-pdf-test-2",
        "name": "audit_findings.pdf",
        "filename": "audit_findings.pdf",
        "type": "pdf",
    }

    markdown_response = """# Compliance & Policy Audit Report

## Executive Overview
The independent compliance audit of core cloud infrastructure was completed successfully.
All Tier-1 controls conform to ISO 27001 and SOC 2 Type II specifications.

| Control Area | Status | Criticality | Owner |
|---|---|---|---|
| Access Management | Verified | High | Security |
| Encryption at Rest | Verified | Critical | Platform |
| Logging & Audit Trail | Verified | Medium | DevOps |

## Actionable Recommendations
- Rotate IAM administrative keys every 90 days.
- Enforce hardware MFA for production database access.
"""

    art = extract_file_artifact_from_turn(
        content=markdown_response,
        agent_id="orchestrator",
        prompt="prepare a report according to /artifact [Compliance & Policy Review]",
        attached_artifacts=[mock_pdf],
    )

    assert art is not None, "File artifact should be generated"
    assert art.get("type") == "pdf", f"Expected type pdf, got {art.get('type')}"
    assert art.get("name", "").endswith(".pdf")
    assert art.get("is_base64") is True
    assert art.get("size_bytes", 0) > 500
    assert bool(art.get("content"))


if __name__ == "__main__":
    print("Running test_artifact_report_workflow_synthesis...")
    test_artifact_report_workflow_synthesis()
    print("✓ test_artifact_report_workflow_synthesis PASSED")

    print("Running test_pdf_document_generator_styling_and_escaping...")
    test_pdf_document_generator_styling_and_escaping()
    print("✓ test_pdf_document_generator_styling_and_escaping PASSED")

    print("Running test_extract_file_artifact_dual_output...")
    test_extract_file_artifact_dual_output()
    print("✓ test_extract_file_artifact_dual_output PASSED")

    print("\n===============================")
    print("ALL PDF REPORT ARTIFACT TESTS PASSED!")
    print("===============================")
