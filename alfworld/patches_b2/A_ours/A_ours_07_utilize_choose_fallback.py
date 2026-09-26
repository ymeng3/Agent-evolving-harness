def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize non-repetitive exploration actions ('look', 'examine') if available
    exploratory_actions = [action for action in admissible if action in ['look', 'examine']]
    if exploratory_actions:
        return exploratory_actions[0]

    # Otherwise, randomly select an admissible action, biased towards diversity when possible
    from random import choice
    recent_actions = state.get('recent_actions', set())
    diverse_action = next((action for action in admissible if action not in recent_actions), None)

    chosen_action = diverse_action if diverse_action else choice(admissible)
    # Update state tracking recent actions to avoid repetition
    recent_actions.add(chosen_action)
    if len(recent_actions) > 3:  # Keep tracking of only a few recent actions
        recent_actions.pop()

    state['recent_actions'] = recent_actions

    return chosen_action