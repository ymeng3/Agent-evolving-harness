import re

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

    return extract_action(response)

def format_prompt(prompt: str, state: dict) -> str:
    split_prompt = (
        prompt.replace("Now it's your turn to take an action.",
                       "Now it's your turn to reason and take an action.")
              .replace("You should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags.",
                       "First, reason step-by-step about the current situation, considering the goal and admissible actions. Enclose this reasoning within <think> </think> tags.")
              .replace("Once you've finished your reasoning, you should choose an admissible action for current step and present it within <action> </action> tags.",
                       "After reasoning, review admissible actions again, then decide and clearly specify your action within <action> </action> tags.")
    )
    return split_prompt