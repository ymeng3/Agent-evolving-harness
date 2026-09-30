EDITS = [
    {
        "id": "e1",
        "capability": "Verification",
        "impl": "ControlFlow",
        "trigger": "after retrieving an API response_schema",
        "depends": [],
        "expected_effect": "Ensure the right schema is used before proceeding with execution",
        "side_effect_risk": "May delay execution if checking large schemas"
    }
]

def e1_post_parse(code, state):
    if 'show_api_doc' in code and 'response_schemas' in code:
        # If response_schemas are retrieved, ensure that they're checked before proceeding
        schema_check_code = """
for schema in doc['response_schemas']['success']:
    if not isinstance(schema, dict) or 'email_thread_id' not in schema:
        raise ValueError("Unexpected response schema structure: missing 'email_thread_id'")
"""
        code += schema_check_code
    return code
