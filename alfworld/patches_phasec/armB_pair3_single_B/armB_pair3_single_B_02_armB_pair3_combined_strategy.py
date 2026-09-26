HISTORY_LENGTH = 8
TEMPERATURE = 0.3

def format_prompt(prompt: str, state: dict) -> str:
    # Adding a reminder at the start of the prompt for the agent to double-check the admissible actions.
    reminder = "Remember to choose an action that is present in the admissible actions list. "
    return reminder + prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Stripping the action response from the model to ensure it matches admissible action formatting.
    import re
    action_match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if action_match:
        return action_match.group(1).strip().lower()
    else:
        return "look"  # Default fallback action in case of parsing failure

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Retry with an extra instruction if the action is invalid. Reduce temperature for consistency.
    if attempt == 1:
        return {
            "extra_instruction": "Ensure the action is valid and in the admissible list. Review and try again.",
            "temperature": 0.2
        }
    elif attempt == 2:
        return {
            "extra_instruction": "Double-check the admissible actions and confirm selection is valid.",
            "temperature": 0.1
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update the state with the last seen observation and action for potential loop detection or strategy adjustment.
    state.setdefault("history", []).append((observation, action))
    # Keep the history within limits for relevant checking
    if len(state["history"]) > 20:
        state["history"].pop(0)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer a no-op like "look" on invalid action but could opt for other common safe actions based on the context here.
    common_safe_actions = ["look", "wait", "turn around"]
    for action in common_safe_actions:
        if action in admissible:
            return action
    return admissible[0]  # fallback to first admissible action if no common safe action is found