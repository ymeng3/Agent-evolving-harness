HISTORY_LENGTH = 20
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    # Introduce additional context through memory integration
    memory_note = state.get("memory_note", "")
    if memory_note:
        prompt += f"\nRemember: {memory_note}"
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    feedback = f"Remember the task requirements and room layout."  # Adding contextual feedback could aid in decision making
    state["memory_note"] = feedback
    if attempt == 1:
        return {"extra_instruction": extra_instruction + "\n" + feedback, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Gather notes to improve future decisions
    if 'Receptacle' in observation:
        state["memory_note"] = "Consider placing in the receptacle if necessary."

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Default to 'look' to gather more information
    return 'look'