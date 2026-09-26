HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory if not already done
    if 'action_history' not in state:
        state['action_history'] = []
    
    # Record the action-observation pair
    state['action_history'].append((action, next_observation))
    
    # Keep memory to a reasonable length to prevent growth (only store the last 20 steps)
    if len(state['action_history']) > 20:
        state['action_history'].pop(0)

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re

    # Extract action from model response
    action_pattern = r"<action>(.*?)</action>"
    action_match = re.search(action_pattern, response, re.DOTALL)
    if action_match:
        proposed_action = action_match.group(1).strip().lower()
        
        # Prevent loops using action history
        recent_actions = [pair[0] for pair in state.get('action_history', [])[-5:]]
        if proposed_action in recent_actions:
            for fallback_action in admissible:
                if fallback_action not in recent_actions:
                    return fallback_action
        
        if proposed_action in admissible:
            return proposed_action

    return admissible[0]  # Defaulting to the first admissible action if no valid action is found