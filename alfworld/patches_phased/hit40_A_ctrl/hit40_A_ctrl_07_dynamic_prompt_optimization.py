HISTORY_LENGTH = 8

def format_prompt(prompt: str, state: dict) -> str:
    # Add dynamic information based on the history to optimize the prompt
    # Emphasize any frequent action and note avoided ones to guide the agent.
    dynamic_feedback = ""
    action_history = state.setdefault('action_history', [])

    if action_history:
        action_counter = collections.Counter(action_history)
        most_common_action, count = action_counter.most_common(1)[0]
        if count > 2:
            dynamic_feedback += f"\nRecently, you often selected '{most_common_action}'. Consider varying your actions."

        avoided_actions = set(admissible) - set(action_history)
        if avoided_actions:
            dynamic_feedback += f" Previously, you haven't chosen: {', '.join(avoided_actions)}."

    return prompt + dynamic_feedback

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Record actions to provide more context in the prompt later
    state.setdefault('action_history', []).append(action)