# TARGET: Reduce the frequency of unnecessary random exploration actions (e.g., "examine") by using a systematic search and navigation strategy.
HISTORY_LENGTH = 7

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on searching systematic areas in sequence to find objects efficiently.
    """
    unexplored_locations = state.get("unexplored_locations", [])
    if unexplored_locations:
        location_guide_str = ", ".join(unexplored_locations)
        prompt += f"\nNote: Consider checking unexplored locations: {location_guide_str}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    # Default fallback action when no valid action is found
    state["fallback_attempts"] += 1
    if state["fallback_attempts"] > 2:
        state["fallback_attempts"] = 0
        state["unexplored_locations"].pop(0) if state["unexplored_locations"] else None
    return "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Use memory to track unexplored locations and systematize navigation.
    """
    if 'unexplored_locations' not in state:
        state['unexplored_locations'] = ["cabinet 1", "cabinet 2", "cabinet 3", "cabinet 4", "cabinet 5", "drawer 1", "drawer 2"]

    # Update unexplored locations if the agent successfully explores
    if action.startswith("go to") and "nothing" not in next_observation:
        location_found = action.split("go to ")[1]
        if location_found in state['unexplored_locations']:
            state['unexplored_locations'].remove(location_found)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Encourage model to focus on unexplored locations and amend exploratory action sequencing on retries.
    """
    if attempt == 1:
        extra_instruction = (
            "When retrying, focus on areas that haven't been fully explored. Refer to the location guide."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Prioritize choosing an action that aligns with unexplored areas or known object locations."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    When no admissible action is available, cycle through unexplored locations or known areas.
    """
    state["fallback_attempts"] = 0
    next_location = state['unexplored_locations'][0] if state['unexplored_locations'] else "look"
    fallback_action = f"go to {next_location}" if f"go to {next_location}" in admissible else "look"
    return fallback_action