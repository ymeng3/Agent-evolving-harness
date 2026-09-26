import re

HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Define a helper function to clean and refine the extracted action
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

    action = extract_action(response)
    if action in admissible:
        state["memory_feedback"] = f"Action '{action}' was successful."
    else:
        state["memory_feedback"] = "Remember to pick actions from the admissible list."
    return action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible. "
            "Ensure to select an action from the admissible list and consider the environment."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3 if attempt == 1 else 0.2}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nNote: {memory_feedback}."
    return prompt