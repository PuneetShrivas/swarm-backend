# QA Checklist: Custom Agent Studio, Enhanced Workflow Testing, AI Generator Mode & Chat UI Sanitization

*Created: 2026-10-28T20:32:00+05:30*  
*Last Updated: 2026-10-28T20:38:00+05:30*  
*Status: Pending Implementation Approval*

## Chat UI Sanitization & Unified Navigation
- [ ] Top navigation bar renders across the app with centered 3-pillar segmented switcher (`💬 Chat` · `🤖 Agents` · `⚡ Workflows`).
- [ ] Switching between Chat, Agents, and Workflows is immediate with persistent state.
- [ ] Chat sidebar is clean: congested 200px agent card widget removed; replaced with a subtle summary link to Agents Studio.
- [ ] Chat sidebar focuses cleanly on conversation sessions history, rename/delete actions, and new chat creation.
- [ ] Chat header is minimalist: title with clean popover agent selector, and compact action icon buttons.
- [ ] Message tool calls and routing delegation traces are collapsed by default into sleek, expandable single-line pills.
- [ ] Clean empty state greeting renders when starting a fresh chat.

## Custom Agent Studio & Playground
- [ ] `/agents` route is accessible and adheres strictly to the Linear design system (`#010102` canvas, `#0f1011` cards, `#23252a` hairline borders, `#5e6ad2` accents).
- [ ] Users can create a new agent via "+ Create Agent" with name, role, system prompt, model, temperature, and attached tools.
- [ ] Agent Playground modal allows providing custom input prompts and mock parameters.
- [ ] Testing an agent displays live markdown response, duration, tokens, and tool invocations.
- [ ] Custom agents appear in the Chat agent selector, Workflow step agent selector, and sidebar roster.
- [ ] Users can edit or delete their custom agents.

## Workflow Step Testing UX
- [ ] Step unit test modal automatically parses `{{...}}` variable tokens in instructions.
- [ ] Fields are auto-generated for each detected variable (e.g. `inputs.query`, `steps.step_1.output.text`).
- [ ] A live "Resolved Prompt Preview" displays what the agent receives.
- [ ] Output inspector cleanly displays status, duration, tokens, markdown content, and tool calls.
- [ ] Switch between visual form and raw JSON mode works smoothly.

## Workflow System Testing
- [ ] Clicking "System Test" opens `WorkflowSystemTestModal`.
- [ ] All required input parameters across all steps in the workflow are discovered.
- [ ] User can provide custom input values for testing.
- [ ] Live execution stepper displays status as each step progresses.
- [ ] Final output and per-step breakdown tabs display accurately.

## AI Generation Mode
- [ ] "✨ Generate with AI" button in Workflows opens `AIWorkflowGeneratorModal`.
- [ ] User enters natural language prompt; AI generates a complete multi-step workflow.
- [ ] Review screen displays title, goal, visual step sequence, and dependencies with option to tweak before saving.
- [ ] Saving immediately opens the workflow in the Workflow Studio.
- [ ] "✨ Generate with AI" button in Agents opens `AIAgentGeneratorModal`.
- [ ] User enters natural language prompt; AI generates persona, role, and comprehensive system prompt.
- [ ] Review screen allows testing or immediately saving the agent.
- [ ] Deterministic fallback functions reliably when Gemini API key is absent.
