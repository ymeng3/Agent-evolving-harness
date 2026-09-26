HISTORY_LENGTH = 7

def format_prompt(prompt: str, state: dict) -> str:
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nNote: {memory_feedback}."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "successfully" in next_observation:
        state["memory_feedback"] = "The last action led to progress. Maintain this approach."
    elif "cannot" in next_observation:
        state["memory_feedback"] = f"Reconsider the approach; the action '{action}' was ineffective."