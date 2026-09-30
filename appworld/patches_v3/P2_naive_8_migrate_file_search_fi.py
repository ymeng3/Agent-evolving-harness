EDITS = [
    {
        "id": "e1",
        "capability": "ToolUse",
        "impl": "ControlFlow",
        "trigger": "on step 0 when task involves migrating files from local backup",
        "depends": [],
        "expected_effect": "Ensure the agent attempts to access the local file system to read the necessary files before proceeding with the account creation and migration",
        "side_effect_risk": "Low, as it just adds a sequence to read local files which is already part of the task"
    }
]

def e1_setup():
    return ""

def e1_pre_call(prompt, state):
    if 'migrate my music library to Spotify' in state.get('task_description', ''):
        return prompt
    return prompt

def e1_post_exec(code, out, state):
    if state.get('step') == 0 and 'migrate my music library to Spotify' in state.get('task_description', ''):
        # Ensure the agent reads files before proceeding
        instructions = '''
print(apis.api_docs.show_api_doc(app_name='file_system', api_name='list_files'))
files = apis.file_system.list_files(directory='~/backups')
print(files)
'''
        state['code'] = instructions + state.get('code', '')

def e1_post_parse(code, state):
    return code

def e1_pre_complete(code, state):
    return code
