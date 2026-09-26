HISTORY_LENGTH = 10

def choose_fallback(admissible: list[str], state: dict) -> str:
    for action in admissible:
        if ('take' in action or 'pick up' in action) and action.split()[-1] not in state['objects_taken']:
            return action
    for action in admissible:
        if 'clean' in action or 'cool' in action or 'heat' in action:
            if action not in state['family_verbs_issued']:
                return action
    return 'look'
