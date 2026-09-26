HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # Increase history length for more context on retry
        state["history_increase"] = True
        return {"extra_instruction": "Please consider the increased history context to decide the best action."}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    if state.get("history_increase"):
        start_idx = prompt.find("Below are the most recent")
        prefix = prompt[:start_idx]
        suffix = prompt[start_idx:].replace(f"{HISTORY_LENGTH}", f"{HISTORY_LENGTH + 5}")
        return prefix + suffix
    return prompt