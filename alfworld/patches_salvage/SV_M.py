def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'objects_taken' not in state:
        state['objects_taken'] = set()
    if 'family_verbs_issued' not in state:
        state['family_verbs_issued'] = set()
    if 'take' in action or 'pick up' in action:
        object_taken = action.split()[-1]
        state['objects_taken'].add(object_taken)
    if any((verb in action for verb in ['clean', 'cool', 'heat'])):
        state['family_verbs_issued'].add(action)
