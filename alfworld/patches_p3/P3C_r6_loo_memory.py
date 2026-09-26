import random

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {'extra_instruction': 'Choose an action from the admissible list and avoid repetitive choices.', 'temperature': 0.5}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    last_actions = state.get('action_history', [])
    if last_actions and len(last_actions) >= 2:
        if last_actions[-1] in admissible and last_actions[-1] == last_actions[-2]:
            alternate_choices = [action for action in admissible if action != last_actions[-1]]
            if alternate_choices:
                return random.choice(alternate_choices)
    move_actions = [action for action in admissible if action.startswith('move')]
    if move_actions:
        return random.choice(move_actions)
    fallback_candidates = ['look', 'move', 'pick', 'open', 'close']
    for action in fallback_candidates:
        for admissible_action in admissible:
            if action in admissible_action:
                return admissible_action
    return random.choice(admissible)
