def format_prompt(prompt: str, state: dict) -> str:
    # Strip away non-essential information after finishing step reasoning.
    # This helps keep the focus on the specific task context and instructs to directly decide on an action.
    if "<think>" in prompt and "</think>" in prompt:
        think_block = prompt.split("<think>")[1].split("</think>")[0]
        preamble = prompt.split("<think>")[0]
        # Trimming thoughts to remove wandering or irrelevant musings.
        # Only keep essential thought lines that may help clarify the action.
        significant_thoughts = "\n".join(
            line for line in think_block.split('\n') if "step" in line or "action" in line
        )
        new_think_block = "<think>" + significant_thoughts + "</think>"
        remaining_prompt = prompt.split("</think>")[1]
        return preamble + new_think_block + remaining_prompt
    
    return prompt