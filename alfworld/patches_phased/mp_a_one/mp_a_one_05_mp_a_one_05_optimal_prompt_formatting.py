HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    # Remove redundant information in prompt and add state-dependent hints based on past failures.
    step_indicators = ["step", "observation", "admissible actions"]
    segments = prompt.split("\n")
    formatted_prompt = "\n".join(
        segment for segment in segments
        if any(indicator in segment.lower() for indicator in step_indicators)
    )

    # Add state-based clues if there were past failures in choosing admissible actions.
    if state.get("past_failures", 0) > 0:
        formatted_prompt += "\nRemember to choose actions that are explicitly listed as admissible."

    return formatted_prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Keep track of past failures to modify prompt for enhanced decision-making cues.
    if "past_failures" not in state:
        state["past_failures"] = 0
    if "Your last action wasn't valid" in next_observation:
        state["past_failures"] += 1