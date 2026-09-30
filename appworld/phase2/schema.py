"""Phase 2 common skeleton (2026-09-28): FailureMechanism -> InterventionAddress -> Edit[] -> Candidate -> Inheritance.
Capabilities: Planning, Memory, ToolUse, Recovery, Verification. Implementations: Prompt, State, Code, ControlFlow.
Control points (bos_appworld_v3): setup, pre_call, post_parse, post_exec, pre_complete."""
CAPS = ["Planning", "Memory", "ToolUse", "Recovery", "Verification"]; IMPLS = ["Prompt", "State", "Code", "ControlFlow"]; POINTS = ["setup", "pre_call", "post_parse", "post_exec", "pre_complete"]
FM_FIELDS = ["scope", "trigger", "observable_evidence", "mechanism", "capability", "implementation", "control_point", "counterevidence"]
EDIT_FIELDS = ["id", "capability", "impl", "trigger", "depends", "expected_effect", "side_effect_risk"]
FM_PROMPT = """You diagnose ONE failed trajectory of an LLM tool-use agent (AppWorld: the agent writes python cells that call app APIs; a task ends when it
calls apis.supervisor.complete_task()). Output a FailureMechanism as JSON with EXACTLY these keys:
 scope: which class of task/state transition this explains (one line);
 trigger: the task state or execution event at which the mechanism applies;
 observable_evidence: what in the code / API outputs / state shows it (quote cell numbers and outputs);
 mechanism: the concrete step where information was lost, a wrong decision was made, or a goal was skipped;
 capability: one of Planning, Memory, ToolUse, Recovery, Verification;
 implementation: one of Prompt, State, Code, ControlFlow (Prompt only if the fix genuinely needs a model-side behaviour change; prefer harness-executed State/Code/ControlFlow);
 control_point: one of setup, pre_call, post_parse, post_exec, pre_complete (where a harness edit would intervene);
 counterevidence: when the same surface behaviour would be correct and no fix should fire.
Generic quality words (e.g. 'context awareness', 'be careful', 'requirements fulfillment') are NOT mechanisms. Be specific and executable."""
