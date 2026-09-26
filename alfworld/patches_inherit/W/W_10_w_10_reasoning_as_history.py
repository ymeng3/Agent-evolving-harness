HISTORY_LENGTH = 8
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    # Adding reasoning history to the state which can improve context for the model
    if "reasoning_history" not in state:
        state["reasoning_history"] = []

    # Insert the reasoning before the prompt
    reasoning_history_text = " ".join(state["reasoning_history"][-2:])  # Use only the last two reasoning states
    return f"{reasoning_history_text}\n{prompt}"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Extract reasoning from the action step and save it
    reasoning = next_observation.split("<think>")[1].split("</think>")[0].strip() if "<think>" in next_observation else ""
    if reasoning:
        state["reasoning_history"].append(reasoning)
    
    # Maintain the reasoning history to a reasonable size
    if len(state["reasoning_history"]) > 5:
        state["reasoning_history"].pop(0)