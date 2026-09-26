HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_effectiveness' not in state:
        state['action_effectiveness'] = {}
    if 'successfully' in next_observation:
        state['action_effectiveness'][action] = state['action_effectiveness'].get(action, 0) + 1
    elif 'cannot' in next_observation and action in state['action_effectiveness']:
        state['action_effectiveness'][action] = max(state['action_effectiveness'][action] - 1, 0)

def format_prompt(prompt: str, state: dict) -> str:
    effective_actions = [action for action, score in state.get('action_effectiveness', {}).items() if score > 1]
    if effective_actions:
        prompt += f"\nRecall: Actions like {', '.join(effective_actions)} were effective previously. Consider similar strategies."
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        instruction = " Your chosen action was not admissible. "
        if 'action_effectiveness' in state:
            recommended_action = max(state['action_effectiveness'], key=state['action_effectiveness'].get, default=None)
            if recommended_action and recommended_action in admissible:
                instruction += f"Note that '{recommended_action}' has been effective before; consider if it's relevant now."
        return {"extra_instruction": instruction, "temperature": 0.3}
    return None