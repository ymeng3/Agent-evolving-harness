EDITS = [
    {
        "id": "e1",
        "capability": "Code",
        "impl": "post_parse",
        "trigger": "fails to locate API method for Simple Note operations",
        "depends": [],
        "expected_effect": "Automatically insert the code to list APIs for Simple Note when the search didn't yield results.",
        "side_effect_risk": "Minimal risk of interference with non-related tasks."
    },
    {
        "id": "e2",
        "capability": "ControlFlow",
        "impl": "pre_call",
        "trigger": "before checking Gmail draft APIs when drafts haven't been properly loaded or filtered",
        "depends": [],
        "expected_effect": "Insert an additional search step for email drafts using specific subject keywords, avoiding reliance on initial faulty search.",
        "side_effect_risk": "Potential duplicate queries if already resolved in code by agent."
    }
]

def e1_post_parse(code, state):
    if 'simple_note' in code and 'export' not in code:
        # Inserting code to discover available APIs for Simple Note
        code_preparation = """descriptions = apis.api_docs.show_api_descriptions(app_name='simple_note')
for desc in descriptions:
    if 'note' in desc['name'].lower():
        print(desc['name'], ':', desc['description'])"""
        return code_preparation + "\n" + code
    return code

def e2_pre_call(prompt, state):
    if "show_drafts" in prompt and "subject" not in prompt:
        # Ensure search includes specific subject keywords
        revised_prompt = prompt.replace("show_drafts(", "show_drafts(query='workout', ")
        return revised_prompt
    return prompt
