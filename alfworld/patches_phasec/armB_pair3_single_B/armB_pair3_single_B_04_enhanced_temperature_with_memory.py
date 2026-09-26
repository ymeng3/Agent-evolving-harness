HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    # Append contextual notes from memory to the prompt for enriched decision-making
    notes = state.get("notes", "")
    return f"{prompt}\nContextual Notes: {notes}"

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    # Extract action from the response using regex
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Increase temperature to encourage exploration on retry attempts
    if attempt == 1:
        return {"extra_instruction": "Try to correct your action choice.", "temperature": 0.6}
    elif attempt == 2:
        return {"extra_instruction": "Please ensure your next action is among the admissible actions.", "temperature": 0.7}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update state with notes on high-level observations or actions
    notes = state.setdefault("notes", "")
    if "clean" in action or "cook" in action:
        notes += f"Recently performed action: {action}. "
    state["notes"] = notes

def choose_fallback(admissible: list[str], state: dict) -> str:
    # A strategy to fall back on the 'look' action by default
    return "look"