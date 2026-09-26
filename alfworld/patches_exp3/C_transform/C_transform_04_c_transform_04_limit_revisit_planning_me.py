HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_locations' not in state:
        state['visited_locations'] = set()
    state['visited_locations'].add(observation)

def format_prompt(prompt: str, state: dict) -> str:
    memory_feedback = ""

    if len(state.get('visited_locations', [])) > 0:
        visited = ", ".join(state['visited_locations'])
        memory_feedback += f"Previously visited locations include: {visited}. "

    return f"{prompt}\n{memory_feedback}Avoid revisiting locations you've already searched unless necessary."

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        instruction = " The previous action was invalid. Avoid repeating ineffective actions. "
        
        if action in state.get('visited_locations', set()):
            admissible = [a for a in admissible if a != action]
            instruction += "Consider paths that differ from the most recent visit. "
        
        if action.startswith("place") and state.get('current_holding', ""):
            instruction += (f"Check relevant objects first. You are currently holding: "
                            f"{state['current_holding']}. ")
        
        if admissible:
            instruction += f"Choose a new strategy. Don't repeat: {action}. "
        
        return {"extra_instruction": instruction, "temperature": 0.4}
    
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_match = re.search(r"<action>\s*(.*?)\s*</action>", response, re.IGNORECASE)
    if action_match:
        action = action_match.group(1).strip().lower()
        if action in admissible:
            if "place" in action:
                state['current_holding'] = action.split()[-1]
            return action
    return "look"