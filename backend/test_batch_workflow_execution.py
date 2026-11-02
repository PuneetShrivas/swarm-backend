"""
Test Suite: Batch Workflow Execution, Mid-Sentence Autocomplete & In-Memory ZIP Compilation

Validates:
1. Mid-sentence /workflow extraction (bracketed and unbracketed syntax).
2. Workflow resolution against memory store and preloaded defaults.
3. Multi-file batch execution with input isolation.
4. In-memory ZIP package structure (outputs/, logs/, batch_execution_summary.md).
5. Chat turn integration returning batch_file_runs metadata and downloadable ZIP artifact.
"""

import sys
import os
import io
import json
import base64
import zipfile

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.main import (
    extract_workflow_candidate_from_prompt,
    resolve_workflow_reference,
    _execute_chat_turn,
    ChatRequest,
    Message,
    workflow_engine,
)
from app.supabase import memory_store
from app.workflows.default_workflows import get_default_workflows


def test_extract_workflow_candidate_from_prompt():
    print("\n--- Test: extract_workflow_candidate_from_prompt ---")
    
    # 1. Bracketed syntax mid-sentence
    cand1 = extract_workflow_candidate_from_prompt(
        "please follow the /workflow [Enterprise File Summarizer] and execute it for all attached files"
    )
    assert cand1 == "Enterprise File Summarizer", f"Expected 'Enterprise File Summarizer', got '{cand1}'"
    print("  [PASS] Bracketed mid-sentence")

    # 2. Short /wf bracketed syntax
    cand2 = extract_workflow_candidate_from_prompt("run /wf [Data Cleaner] now")
    assert cand2 == "Data Cleaner", f"Expected 'Data Cleaner', got '{cand2}'"
    print("  [PASS] /wf bracketed")

    # 3. Natural unbracketed mid-sentence syntax
    cand3 = extract_workflow_candidate_from_prompt(
        "follow the /workflow Competitive Research and execute it for all attached files"
    )
    assert cand3 == "Competitive Research", f"Expected 'Competitive Research', got '{cand3}'"
    print("  [PASS] Natural unbracketed mid-sentence")

    # 4. Starting with /workflow
    cand4 = extract_workflow_candidate_from_prompt("/workflow Invoice Extractor")
    assert cand4 == "Invoice Extractor", f"Expected 'Invoice Extractor', got '{cand4}'"
    print("  [PASS] Standard prefix command")


def test_resolve_workflow_reference():
    print("\n--- Test: resolve_workflow_reference ---")
    
    # Resolve against default preloaded workflow
    wf = resolve_workflow_reference("Competitive Research & Report Pipeline", "guest-user")
    assert wf is not None, "Expected to resolve Competitive Research & Report Pipeline"
    assert "Competitive Research" in wf["title"]
    print(f"  [PASS] Exact title match: {wf['title']}")

    # Partial substring match
    wf_partial = resolve_workflow_reference("Competitive Research", "guest-user")
    assert wf_partial is not None, "Expected to resolve via partial title"
    assert wf_partial["id"] == wf["id"]
    print(f"  [PASS] Partial title match: {wf_partial['title']}")

    # ID match
    wf_id = resolve_workflow_reference(wf["id"], "guest-user")
    assert wf_id is not None, "Expected to resolve via ID"
    assert wf_id["id"] == wf["id"]
    print(f"  [PASS] ID match: {wf_id['id']}")


def test_batch_workflow_execution_and_zip_artifact():
    print("\n--- Test: test_batch_workflow_execution_and_zip_artifact ---")

    # Setup simulated attached files
    attached_files = [
        {
            "id": "file-1",
            "name": "sales_q1.csv",
            "filename": "sales_q1.csv",
            "type": "csv",
            "content": "Quarter,Revenue,Profit\nQ1,100000,25000",
        },
        {
            "id": "file-2",
            "name": "sales_q2.csv",
            "filename": "sales_q2.csv",
            "type": "csv",
            "content": "Quarter,Revenue,Profit\nQ2,120000,32000",
        },
        {
            "id": "file-3",
            "name": "sales_q3.csv",
            "filename": "sales_q3.csv",
            "type": "csv",
            "content": "Quarter,Revenue,Profit\nQ3,145000,41000",
        },
    ]

    prompt = "follow the /workflow [Competitive Research & Report Pipeline] and execute it for all attached files"
    
    req = ChatRequest(
        messages=[Message(role="user", content=prompt)],
        attached_artifacts=attached_files,
        artifact_ids=["file-1", "file-2", "file-3"],
    )

    original_execute = workflow_engine.execute_workflow

    def mock_execute(workflow_data, inputs, user_id, trigger_type, session_id=None, step_callback=None, is_ephemeral=False):
        fname = inputs.get("filename", "file.csv")
        return {
            "id": f"run-{fname}",
            "status": "completed",
            "duration_ms": 150.0,
            "total_tokens": 520,
            "output_data": {
                "final_result": f"Report generated successfully for {fname}. Metrics: processed revenue and profit data."
            },
            "step_runs": [
                {
                    "step_id": "step_1",
                    "step_index": 0,
                    "agent_id": "data_analyst",
                    "status": "completed",
                    "duration_ms": 150.0,
                    "tokens_used": 520,
                    "output_data": {"text": f"Parsed {fname}"},
                }
            ],
            "artifacts": [],
        }

    workflow_engine.execute_workflow = mock_execute
    try:
        msg = _execute_chat_turn(req, current_user=None)
    finally:
        workflow_engine.execute_workflow = original_execute
    
    assert msg.role == "agent"
    meta = msg.metadata or {}

    # Check batch execution metadata
    assert meta.get("mode") == "batch_workflow_execution", f"Expected mode=batch_workflow_execution, got {meta.get('mode')}"
    assert meta.get("is_batch_workflow") is True, "Expected is_batch_workflow=True"
    assert meta.get("total_files") == 3, f"Expected total_files=3, got {meta.get('total_files')}"
    
    batch_runs = meta.get("batch_file_runs", [])
    assert len(batch_runs) == 3, f"Expected 3 batch_file_runs, got {len(batch_runs)}"

    for idx, r in enumerate(batch_runs):
        assert r["file_index"] == idx
        assert r["file_name"] == attached_files[idx]["filename"]
        assert r["status"] == "completed"
        assert len(r.get("output_text", "")) > 0
        print(f"  [PASS] File {idx+1} run: {r['file_name']} -> {r['status']} ({r['duration_ms']}ms)")

    # Check downloadable ZIP file artifact
    zip_artifact = meta.get("file_artifact")
    assert zip_artifact is not None, "Expected file_artifact in metadata"
    assert zip_artifact.get("type") == "zip", f"Expected type=zip, got {zip_artifact.get('type')}"
    assert zip_artifact.get("mime_type") == "application/zip"
    assert zip_artifact.get("is_base64") is True
    assert zip_artifact.get("downloadable") is True
    assert zip_artifact.get("filename", "").endswith(".zip")

    # Unpack and verify zip archive contents
    zip_b64 = zip_artifact["content"]
    raw_bytes = base64.b64decode(zip_b64)
    with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as zf:
        namelist = zf.namelist()
        print(f"  [INFO] ZIP Namelist: {namelist}")
        
        # Verify root summary
        assert "batch_execution_summary.md" in namelist, "Missing batch_execution_summary.md"
        summary_content = zf.read("batch_execution_summary.md").decode("utf-8")
        assert "Batch Workflow Execution Summary" in summary_content
        assert "sales_q1.csv" in summary_content
        assert "sales_q2.csv" in summary_content
        assert "sales_q3.csv" in summary_content
        
        # Verify outputs and logs for each file
        for f in attached_files:
            stem = f["filename"].split(".")[0]
            out_file = f"outputs/{stem}_result.md"
            log_file = f"logs/{stem}_execution_log.json"
            assert out_file in namelist, f"Missing {out_file} in zip"
            assert log_file in namelist, f"Missing {log_file} in zip"
            
            # Check log json format
            log_data = json.loads(zf.read(log_file).decode("utf-8"))
            assert log_data["file_name"] == f["filename"]
            assert log_data["status"] == "completed"

    print("  [PASS] In-memory ZIP compilation and structure validation")


if __name__ == "__main__":
    test_extract_workflow_candidate_from_prompt()
    test_resolve_workflow_reference()
    test_batch_workflow_execution_and_zip_artifact()
    print("\nALL BATCH WORKFLOW TESTS PASSED SUCCESSFULLY!")
