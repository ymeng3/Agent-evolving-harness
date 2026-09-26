HISTORY_LENGTH = 8
TEMPERATURE = 0.3

import re
import random


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your previous choice wasn't valid. Please select from the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None


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

        return random.choice(admissible)

    return extract_action(response)


def format_prompt(prompt: str, state: dict) -> str:
    if state.get("focus_mode"):
        prompt += " Remember, precision and following admissible actions are crucial."
    return prompt


def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state["last_action"] = action

    def detect_loops(state: dict) -> bool:
        return state.get("last_action") == action

    state["focus_mode"] = detect_loops(state)
    
    if state["focus_mode"]:
        state["focus_counter"] = state.get("focus_counter", 0) + 1
        if state["focus_counter"] > 2:
            state["focus_mode"] = False
            state["focus_counter"] = 0