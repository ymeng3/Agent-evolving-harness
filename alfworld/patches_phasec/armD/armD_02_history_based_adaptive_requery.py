HISTORY_LENGTH = 5

def format_prompt(prompt: str, state: dict) -> str:
    if 'recent_action' in state:
        prompt += f"\nIn your previous actions, you chose to {state['recent_action']}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_match = re.search(r"<action>(.*?)</action>", response)
    action = action_match.group(1).strip().lower() if action_match else ""
    state['recent_action'] = action
    return action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "The action must strictly be one of the admissible actions. Please prioritize actions leading to significant progress."
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2 and state.get('recent_action'):
        extra_instruction = f"Consider an alternative to the previous action '{state['recent_action']}' that might achieve progress."
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track action history to identify repeated actions
    if 'action_history' not in state:
        state['action_history'] = []
    state['action_history'].append(action)
    
    # Detect loops or stagnation
    if len(state['action_history']) > 3:
        if len(set(state['action_history'][-3:])) == 1:
            state['loop_detected'] = True
        else:
            state['loop_detected'] = False

def choose_fallback(admissible: list[str], state: dict) -> str:
    if state.get('loop_detected'):
        return admissible[random.randint(0, len(admissible) - 1)]
    return 'look'