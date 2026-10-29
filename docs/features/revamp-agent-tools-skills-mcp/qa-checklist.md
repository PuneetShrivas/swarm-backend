# QA Checklist: Revamp Default Agent Tools, Skills, and MCP Execution Engine

- **Feature Slug**: `revamp-agent-tools-skills-mcp`
- **Datetime**: 2026-10-29T16:02:15+05:30

## Verification Checklist

### Agent Tools & Skills
- [x] `coder`: Has 5 functional tools (`syntax_validator`, `generate_test_suite`, `diff_patcher`, `execute_python_sandbox`, `format_code`) and 5 skills.
- [x] `data_analyst`: Has 6 functional tools (`calculate_statistics`, `format_csv_table`, `correlate_variables`, `linear_forecast`, `parse_tabular_csv`, `detect_anomalies`) and 4 skills.
- [x] `file_creator`: Has 4 functional tools (`generate_file_artifact`, `render_template_file`, `create_tabular_dataset`, `package_multi_file_archive`) and 3 skills.
- [x] `file_parser`: Has 4 functional tools (`parse_document_payload`, `extract_json_schema`, `analyze_csv_delimiter`, `validate_ast_syntax`) and 3 skills.
- [x] `general_assistant`: Has 4 functional tools (`general_lookup`, `clarify_intent`, `summarize_dialogue`, `format_response_structure`), 4 skills, and 1 MCP connector.
- [x] `orchestrator`: Has 4 functional tools (`swarm_router`, `swarm_delegate`, `generate_workflow_dag`, `evaluate_consensus`) and 4 skills.
- [x] `researcher`: Has 5 functional tools (`web_search_query`, `extract_citations`, `fact_check`, `market_quote_lookup`, `rate_source_credibility`) and 4 skills.
- [x] `reviewer`: Has 5 functional tools (`security_audit`, `complexity_analysis`, `dependency_security_scan`, `owasp_compliance_audit`, `test_coverage_estimator`) and 4 skills.
- [x] `synthesizer`: Has 6 functional tools (`generate_executive_summary`, `format_readme`, `create_table_of_contents`, `lint_and_format_markdown`, `extract_action_items`, `generate_changelog_entry`) and 4 skills.

### MCP Infrastructure & Execution
- [x] `backend/app/mcp/manager.py` provides native sandboxed executors for all 12 MCP servers.
- [x] `BaseAgent.execute_mcp_tool` checks agent MCP access configuration and dispatches tool execution.
- [x] `POST /api/agents/{agent_id}/tools/{tool_name}/execute` executes tools with arguments and returns results.
- [x] `POST /api/agents/{agent_id}/mcp/{server_name}/tools/{tool_name}/execute` executes agent MCP tools.
- [x] `GET /api/mcp/servers` lists all 12 registered servers and their exposed tools.
- [x] `POST /api/mcp/execute` allows direct execution of MCP tools.

### Frontend Usability & Interactive Runner
- [x] `AgentDetailsModal.tsx` contains interactive "Test Tool" drawer under the Tools tab.
- [x] Sample parameters are auto-generated based on the tool's JSON schema properties.
- [x] Real-time output inspection with syntax formatting and error badges.
- [x] "Run Tool" test panels for each exposed MCP tool under the MCP Servers tab.
- [x] Clean Next.js build with 0 TypeScript/ESLint errors.
