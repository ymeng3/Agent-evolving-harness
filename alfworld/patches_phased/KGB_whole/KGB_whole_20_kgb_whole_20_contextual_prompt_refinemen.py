HISTORY_LENGTH = 10
TEMPERATURE = 0.3  # Slightly reduce temperature for more focused responses

import re

def format_prompt(prompt: str, state: dict) -> str:
    # Define a helper function to transform and enrich the prompt with context
    def enrich_prompt(original_prompt: str) -> str:
        lines = original_prompt.splitlines()
        # Insert additional context about the task and previous observations, if any
        task_info = "Remember, your task might involve manipulation and placement of objects, cool down or heat up processes, and keen observation."
        reminder = "Always cross-reference your previous observations before deciding on an action."
        enriched_lines = lines[:-1] + [task_info, reminder, lines[-1]]
        return "\n".join(enriched_lines)

    # Return the enriched prompt
    return enrich_prompt(prompt)


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Focus on the admissible actions provided. Your choice must be among these options."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}  # Lower temperature for retry
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}  # Further reduce temperature
    return None


def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Define a helper function to clean and refine the extracted action
    def extract_action(text: str) -> str:
        # Search for the first action enclosed in <action> tags with a more forgiving pattern
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        # If no valid match is found within tags, attempt to match actions directly from the text
        for action in admissible:
            if action in text.lower():
                return action
        
        # If no action is found, return the default fallback action 'look'
        return "look"

    # Extract and return the refined action
    return extract_action(response)