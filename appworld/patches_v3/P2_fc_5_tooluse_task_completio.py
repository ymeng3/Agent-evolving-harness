EDITS = [
    {
        "id": "e1",
        "capability": "ToolUse",
        "impl": "ControlFlow",
        "trigger": "After successful attachment upload when 'complete_task()' has not been called",
        "depends": [],
        "expected_effect": "Ensure task completion by calling complete_task() after attachments are uploaded.",
        "side_effect_risk": "Minimal, as it only triggers after attachment upload indicating nearing task completion."
    }
]

def e1_pre_complete(code, state):
    if not state.get("task_completed", False) and "upload_attachments_to_draft" in code:
        # Automatically append a call to complete_task at the end of the code if it hasn't been called yet.
        return code + "\napis.supervisor.complete_task()"
    return code

def e1_post_exec(code, out, state):
    # Observing successful attachment upload to possibly set task as complete
    if "upload_attachments_to_draft" in code and "Uploaded attachments." in out:
        state["task_completed"] = False
