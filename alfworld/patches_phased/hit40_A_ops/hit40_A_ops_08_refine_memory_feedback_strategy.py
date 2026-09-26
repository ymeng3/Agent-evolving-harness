def format_prompt(prompt: str, state: dict) -> str:
    # Include memory feedback in the prompt to remind the agent of past successes
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nMemory Note: {memory_feedback}"
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update memory based on the success indicator within the observation
    # Simplify feedback to focus on recent successful actions
    if "successfully" in next_observation or "completed" in next_observation:
        state["memory_feedback"] = f"Recent successful action: '{action}'. Consider similar actions."
    elif "failed" in next_observation or "cannot" in next_observation:
        state["memory_feedback"] = f"Action '{action}' didn't work. Reconsider this approach."

# Refactored memory feedback mechanism to reduce repetitive action feedback noise