HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    if 'admissible_priority' not in state:
        state['admissible_priority'] = 0
    # Increase focus on using admissible actions initially in reasoning
    admissible_start = "<think>" in prompt and prompt.index("<think>") < prompt.index("Your admissible actions")
    return prompt if not admissible_start else prompt.replace(
        "<think>", f"<think>Remember to prioritize actions from the admissible list: [{prompt.split('Your admissible actions of the current situation are: ')[1].split('].')[0]}]. ")

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed. Please think carefully while considering these options first."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Keep track of the priority given to admissibles in reasoning to refine future prompts
    if '<think>' in observation:
        thinking_section = observation.split('<think>')[1].strip().split('</think>')[0]
        if any(admissible_action in thinking_section for admissible_action in state.get('admissible_actions', [])):
            state['admissible_priority'] += 1
    
    # Retain the admissible actions for reasoning analysis
    state['admissible_actions'] = next_observation[next_observation.index("[")+1:next_observation.index("]")].split(', ')