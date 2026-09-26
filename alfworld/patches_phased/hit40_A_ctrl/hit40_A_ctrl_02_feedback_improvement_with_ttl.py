HISTORY_LENGTH = 7

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if not state.get('feedback'):
        state['feedback'] = {}

    feedback = f"Action '{action}' resulted in - {next_observation[:50]}"
    state['feedback'][action] = (feedback, 3)  # time-to-live of 3 steps

    # Update TTL for all feedback and remove expired feedback
    remove_keys = []
    for k in state['feedback']:
        feedback, ttl = state['feedback'][k]
        if k != action:  # Don't decrease the TTL for the current action
            ttl -= 1
            if ttl <= 0:
                remove_keys.append(k)
            else:
                state['feedback'][k] = (feedback, ttl)
    for k in remove_keys:
        del state['feedback'][k]

def format_prompt(prompt: str, state: dict) -> str:
    feedback_summary = "\n".join([f for f, ttl in state['feedback'].values()])
    if feedback_summary:
        prompt += f"\n*** Feedback Summary ***: {feedback_summary}"
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    return "look"