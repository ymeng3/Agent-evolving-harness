HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Consider actions similar to previous successes: {action_guide}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["action_guide"] = action
            return action
    # Attempt to recommend a similar action if the response isn't admissible
    recommended_action = next((a for a in admissible if a in response.lower()), None)
    return recommended_action if recommended_action else "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        if len(state['action_success']) >= 3:
            most_recent_actions = state['action_success'][-3:]
            if all(a == most_recent_actions[0] for a in most_recent_actions):
                state['action_guide'] = most_recent_actions[0]

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = (
            "Recall the guidance on successful actions. Focus on choosing from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Choose an action from admissible options that aligns with previous successes."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None