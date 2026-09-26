HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    if "prompt_extra_instruction" not in state:
        state["prompt_extra_instruction"] = ""
    if "step_count_reminder" not in state:
        state["step_count_reminder"] = ""
    # Add reinforcement based on previous success rate
    prev_success_rate = state.get("prev_success_rate", 0.358)
    state["prompt_extra_instruction"] = (
        "You should aim to improve the success rate above {:.2f}.".format(prev_success_rate)
    )
    state["step_count_reminder"] = (
        "Please remember you've taken {} step(s) successfully so far.".format(state.get("successful_steps", 0))
    )
    # Reinforcement message concatenation
    reinforcement_message = state["prompt_extra_instruction"] + " " + state["step_count_reminder"]
    
    # Format the prompt to include reinforcement message
    return prompt + "\n" + reinforcement_message

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 3:
        # Reattempt with reminder on successful steps and extra instruction
        return {
            "extra_instruction": state["step_count_reminder"],
            "temperature": 0.35 if attempt == 1 else 0.3
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Example of tracking successful steps
    if action in next_observation: # simplification assumption: matching successful action in next observation
        state["successful_steps"] = state.get("successful_steps", 0) + 1

    # Update previous success rate with dynamic approximation (simplified)
    total_steps = state.get("total_steps", 0) + 1
    successful_steps = state.get("successful_steps", 0)
    state["prev_success_rate"] = successful_steps / total_steps
    state["total_steps"] = total_steps