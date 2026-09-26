HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    notes = state.get("important_notes", "")
    if notes:
        prompt += f"\n\nRemember these important notes based on observations: {notes}"
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "receptacle" in observation.lower():
        state["important_notes"] = "Remember to interact with receptacles when necessary."
    elif "light" in observation.lower():
        state["important_notes"] = "Ambient lighting might affect visibility."