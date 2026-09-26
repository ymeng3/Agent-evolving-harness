HISTORY_LENGTH = 12
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    memory_insight = state.get("memory_insight", "")
    if memory_insight:
        prompt += f"\nNote from memory: {memory_insight}."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_locations' not in state:
        state['visited_locations'] = set()
    
    state['visited_locations'].add(observation)

    insights = [f"Consider past observations like: {loc}" for loc in state['visited_locations']]
    state['memory_insight'] = " | ".join(insights)

    # Remove distant past observations to keep memory concise
    if len(state['visited_locations']) > 5:
        state['visited_locations'].pop()

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {
            "extra_instruction": "Review recent steps and focus on the task's context to optimize action choice.",
            "temperature": TEMPERATURE
        }
    return None