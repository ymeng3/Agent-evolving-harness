import re

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
        
        return "look"

    return extract_action(response)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        action_suggestion = next((a for a in admissible if a in response.lower()), None)
        extra_instruction = (
            "Your previous action was not admissible."
            " Review the admissible actions: "
            f"{admissible}. If you meant to take a different action such as '{action_suggestion}', ensure it's admissible."
            " Reason carefully considering both your goal and environment."
        )
        return {"extra_instruction": extra_instruction}
    return None