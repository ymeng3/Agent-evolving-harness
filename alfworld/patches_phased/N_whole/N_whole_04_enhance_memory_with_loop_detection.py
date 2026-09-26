HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    def extract_action(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        for action in admissible:
            if action in text.lower():
                return action
        
        return "look"

    return extract_action(response)

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    observations = state.setdefault('observations', [])
    actions = state.setdefault('actions', [])
    
    if len(observations) >= 10:
        observations.pop(0)
        actions.pop(0)
    
    observations.append(observation)
    actions.append(action)

    if len(actions) > 3 and len(set(actions[-3:])) == 1:
        state['loop_detected'] = True
    else:
        state['loop_detected'] = False
    
    if state['loop_detected']:
        state['actions'][-1] = 'look'