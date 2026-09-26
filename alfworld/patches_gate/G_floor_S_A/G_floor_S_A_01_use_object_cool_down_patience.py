def format_prompt(prompt: str, state: dict) -> str:
    # Enhance the prompt to remind the model to have patience if the task involves cooling down objects
    if "cool" in prompt.lower() and "waiting" not in state:
        patience_instruction = (
            "When cooling objects, remember to use 'wait' to allow enough time for cooling."
        )
        state["waiting"] = False
        prompt += f"\n{patience_instruction}"
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action == "wait":
            state["waiting"] = True
        return action if action in admissible else ""
    return ""

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Clear waiting state if the next observed state suggests cooling has occurred
    if "cooled" in next_observation:
        state["waiting"] = False