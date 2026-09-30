EDITS = [
    {
        "id": "e1",
        "capability": "Verification",
        "impl": "Code",
        "trigger": "Before processing threads to determine reminders",
        "depends": [],
        "expected_effect": "Filter out threads that have already received reminders",
        "side_effect_risk": "Minimal, as it only filters based on clear criteria"
    }
]

def e1_pre_call(prompt, state):
    import re

    # Extract relevant thread information from prompt, just before determining emails to send reminders to.
    if "Threads needing a reminder" in prompt:
        lines = prompt.split("\n")
        threads = {}
        already_reminded = set()
        to_remind_pattern = re.compile(r"\d+")
        
        for line in lines:
            if "Threads needing a reminder" in line:
                idx = lines.index(line)
                while idx + 1 < len(lines) and lines[idx + 1].startswith("#"):
                    idx += 1
                    match = to_remind_pattern.search(lines[idx])
                    if match:
                        thread_id = int(match.group())
                        if "already have reminders" not in lines[idx]:
                            threads[thread_id] = None
                        else:
                            already_reminded.add(thread_id)
                break

        # Filter out threads already reminded
        to_remind = {tid: None for tid in threads.keys() if tid not in already_reminded}

        # Update the prompt's information
        updated_prompt_lines = [
            line for line in lines if "Threads needing a reminder" not in line and not line.startswith("# ")
        ]

        new_threads_info = [f"# {tid}" for tid in to_remind.keys()]
        
        updated_prompt = '\n'.join(updated_prompt_lines) + '\n' + '\n'.join(new_threads_info)
        return updated_prompt
    
    return prompt
