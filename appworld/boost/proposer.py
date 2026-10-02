"""Self-proposer: the executor model itself (Qwen3.8-27B on the local vLLM server), thinking ON for proposing. No stronger model."""
import os, re, time


_MOCK = [  # offline tests only (BOOST_MOCK=1): canned replies, including one that fails validation
    "NAME: uses_pagination\nDESCRIPTION: reads more than the first page of results\n```python\ndef detect(steps):\n    return float(any('page_index' in s['code'] for s in steps))\n```",
    "NAME: broken\nDESCRIPTION: raises\n```python\ndef detect(steps):\n    return 1 / 0\n```",
    "NAME: error_burst\nDESCRIPTION: three failed cells in a row\n```python\ndef detect(steps):\n    run = 0\n    for s in steps:\n        run = run + 1 if s['error'] else 0\n        if run >= 3: return 1.0\n    return 0.0\n```",
    "NAME: login_first\nDESCRIPTION: logs in within the first three cells\n```python\ndef detect(steps):\n    return float(any('login' in s['code'] for s in steps[:3]))\n```",
]
_mock_i = [0]


def chat(messages, max_tokens=16000, temperature=0.7, thinking=True, retries=4):
    if os.environ.get("BOOST_MOCK") == "1":
        _mock_i[0] += 1
        if "CRITERION:" in messages[-1]["content"]:
            sem = ["NAME: reads_more_pages\nCRITERION: The agent requests a later page of results (page_index) before acting on a list.",
                   "NAME: short\nCRITERION: too short", "NAME: retries_after_error\nCRITERION: After a failed cell the agent changes the call instead of repeating it."]
            return sem[_mock_i[0] % len(sem)], {"in": 0, "out": 0, "finish": "mock"}
        return _MOCK[_mock_i[0] % len(_MOCK)], {"in": 0, "out": 0, "finish": "mock"}
    from openai import OpenAI
    cl = OpenAI(api_key=os.environ["BOS_API_KEY"], base_url=os.environ["BOS_BASE_URL"], timeout=float(os.environ.get("BOOST_TIMEOUT", "1800")), max_retries=0)
    last = None
    for att in range(retries):
        try:
            kw = {"enable_thinking": thinking}
            if thinking and os.environ.get("BOOST_EFFORT"): kw["reasoning_effort"] = os.environ["BOOST_EFFORT"]   # xhigh (template default) | medium | low
            r = cl.chat.completions.create(model=os.environ.get("BOS_MODEL", "qwen/qwen3.8-27b"), messages=messages, temperature=temperature, max_tokens=max_tokens,
                                           extra_body={"chat_template_kwargs": kw})
            return r.choices[0].message.content or "", {"in": r.usage.prompt_tokens, "out": r.usage.completion_tokens, "finish": r.choices[0].finish_reason}
        except Exception as e:
            last = e; time.sleep(5 * (att + 1))
    raise RuntimeError(f"proposer call failed: {last}")


def last_block(text, must_contain=None):
    """last fenced python block (optionally containing a marker); tolerates a final unclosed fence."""
    blocks = re.findall(r"```(?:python)?[ \t]*\n(.*?)```", text, re.S)
    if text.count("```") % 2 == 1:   # a genuinely unclosed final fence; otherwise prose after a closing fence would be taken as code
        tail = re.search(r"```(?:python)?[ \t]*\n((?:(?!```).)*)$", text, re.S)
        if tail: blocks.append(tail.group(1))
    blocks = [b for b in blocks if must_contain is None or must_contain in b]
    return blocks[-1].strip() + "\n" if blocks else None


def safe_chat(messages, **kw):
    """never raises: a proposer outage becomes an empty reply (an invalid candidate) instead of killing an unattended run."""
    try: return chat(messages, **kw)
    except Exception as e: return "", {"in": 0, "out": 0, "finish": f"error: {str(e)[:120]}"}


def field(text, name):
    m = re.findall(rf"^\s*{name}\s*:\s*(.+)$", text, re.M)
    return m[-1].strip() if m else ""
