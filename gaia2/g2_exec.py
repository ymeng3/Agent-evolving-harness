"""Gaia2 (ARE) action layer: one python code cell per step, ARE tools bound as functions named by their public name (App__tool).

Pure python (no ARE / AppWorld import): tools are duck-typed like are.simulation.tool_utils.AppTool -- _public_name (fallback name),
_public_description / function_description, app_name, args[AppToolArg: name, arg_type, description, has_default, default], return_type,
return_description, write_operation, __call__. Every attribute is optional and read with getattr.
extract_code / validate_code / readonly are copies of appworld/bos_appworld_v3.py (that module cannot be imported in are-env).

    python gaia2/g2_exec.py --selftest
"""
import ast, builtins, contextlib, difflib, io, linecache, os, re, signal, sys, threading, traceback

# ---------------------------------------------------------------- model reply parsing
def strip_think(text):
    """-> (answer after the last </think>, thinking). An unterminated <think> (reply cut off while thinking) -> ("", text)."""
    text = text or ""
    if "</think>" in text:
        thinking, _, answer = text.rpartition("</think>")
        thinking = thinking.replace("<think>", "").strip()
        if "<think>" in answer:   # a second think block that never closed: its content is thinking, not answer
            answer, _, extra = answer.partition("<think>"); thinking = (thinking + "\n" + extra.strip()).strip()
        return answer.strip(), thinking
    if "<think>" in text: return "", text
    return text.strip(), ""


def extract_code(resp):
    """= bos_appworld_v3.extract_code_v2: the LAST closed ```python block (the final answer comes after any reasoning drafts); else the
    last closed ``` block; else the text after a final unclosed fence (usually truncated, so validate_code will reject it unless it
    happens to be complete)."""
    for pat in (r"```python[ \t]*\n(.*?)```", r"```[a-z]*[ \t]*\n(.*?)```"):
        blocks = re.findall(pat, resp, re.S)
        if blocks: return blocks[-1].strip()
    if resp.count("```") % 2 == 1:
        m = re.search(r"```(?:python)?[ \t]*\n((?:(?!```).)*)$", resp, re.S)
        if m: return m.group(1).strip()
    return ""


def validate_code(code):
    """= bos_appworld_v3.validate_code: -> reason string if the code must not be executed, else ''."""
    if not code.strip(): return "your reply contained no ```python code block"
    try: tree = ast.parse(code)
    except SyntaxError as e: return f"the code block is incomplete or not valid Python (SyntaxError: {e.msg}, line {e.lineno}); the reply was probably cut off"
    if any(isinstance(n, ast.Constant) and n.value is Ellipsis for n in ast.walk(tree)): return "the code contains a '...' placeholder instead of real values"
    return ""


def readonly(code, write_names):
    """True iff the cell mentions no write tool. Conservative word match (aliases, comments and strings count as a mention), so a cell
    is only treated as read-only (e.g. a duplicate that may be blocked) when it cannot possibly call a write tool."""
    w = set(write_names or ())
    return not (w & set(re.findall(r"[A-Za-z_]\w*", code)))


# ---------------------------------------------------------------- tool metadata
def tool_name(tool):
    return getattr(tool, "_public_name", None) or getattr(tool, "name", None) or getattr(tool, "__name__", None) or repr(tool)


def tool_app(tool):
    return getattr(tool, "app_name", None) or tool_name(tool).split("__")[0]


def tool_desc(tool):
    return getattr(tool, "_public_description", None) or getattr(tool, "function_description", None) or ""


def _type_str(t):
    if t is None: return ""
    if isinstance(t, type): return t.__name__
    return str(t).replace("typing.", "")


def _default_str(d):
    r = repr(d)
    return r if len(r) <= 20 else "<default>"


def tool_sig(tool):
    """"App__tool(a:str*, b:int=3) -> ret" (* = required)."""
    ps = []
    for a in getattr(tool, "args", None) or []:
        s = str(getattr(a, "name", "?")); t = _type_str(getattr(a, "arg_type", None))
        if t: s += ":" + t
        s += ("=" + _default_str(getattr(a, "default", None))) if getattr(a, "has_default", False) else "*"
        ps.append(s)
    rt = _type_str(getattr(tool, "return_type", None))
    return f"{tool_name(tool)}({', '.join(ps)})" + (f" -> {rt}" if rt else "")


def tool_doc(tool):
    """full documentation, printed by help("App__tool")."""
    lines = [tool_sig(tool), "", tool_desc(tool).strip() or "(no description)"]
    args = getattr(tool, "args", None) or []
    if args:
        lines += ["", "Args:"]
        for a in args:
            t = _type_str(getattr(a, "arg_type", None))
            req = f"optional, default {getattr(a, 'default', None)!r}" if getattr(a, "has_default", False) else "required"
            lines.append(f"  {getattr(a, 'name', '?')} ({t + ', ' if t else ''}{req}): {getattr(a, 'description', None) or ''}".rstrip())
    rt, rd = _type_str(getattr(tool, "return_type", None)), getattr(tool, "return_description", None)
    if rt or rd: lines += ["", f"Returns: {rt}{' -- ' if rt and rd else ''}{rd or ''}"]
    wo = getattr(tool, "write_operation", None)
    if wo is not None: lines.append(f"Write operation: {'yes' if wo else 'no'}")
    return "\n".join(lines)


def format_tool_index(tools, hidden=None):
    """one line per tool, grouped by app (apps and tools in the given order):  App__tool(a:str*, b:int=3) -> ret  # desc[:90]"""
    hidden = set(hidden or ()); groups = {}
    for t in tools:
        if tool_name(t) in hidden: continue
        groups.setdefault(tool_app(t), []).append(t)
    out = []
    for app, ts in groups.items():
        out.append(f"## {app}")
        for t in ts:
            d = " ".join(tool_desc(t).split())[:90].rstrip()
            out.append(tool_sig(t) + (f"  # {d}" if d else ""))
    return "\n".join(out)


# ---------------------------------------------------------------- executor
class CellTimeout(Exception):
    pass
CellTimeout.__module__ = "builtins"   # traceback shows "CellTimeout: ...", not "gaia2.g2_exec.CellTimeout"


def clock_modules(clock):
    """-> {"time": shim, "datetime": shim} for model code: wall-clock reads return the simulation's virtual clock (clock() = epoch
    seconds; naive datetimes are UTC, as the apps show them), so cells are deterministic and see the scenario's date. time.sleep is
    refused (it would only burn wall time): waiting is SystemApp__wait_for_notification. Everything else is the real module."""
    import datetime as _dt, time as _time, types
    tz = _dt.timezone.utc

    class datetime(_dt.datetime):
        @classmethod
        def now(cls, tz_=None):
            return cls.fromtimestamp(clock(), tz_) if tz_ is not None else cls.fromtimestamp(clock(), tz).replace(tzinfo=None)

        @classmethod
        def utcnow(cls): return cls.fromtimestamp(clock(), tz).replace(tzinfo=None)

        @classmethod
        def today(cls): return cls.now()

    class date(_dt.date):
        @classmethod
        def today(cls):
            d = _dt.datetime.fromtimestamp(clock(), tz); return cls(d.year, d.month, d.day)

    dtm = types.ModuleType("datetime"); dtm.__dict__.update({k: v for k, v in vars(_dt).items() if not k.startswith("__")})
    dtm.datetime, dtm.date = datetime, date

    def sleep(seconds=0):
        raise RuntimeError("time.sleep() is disabled in this environment (it does not move the simulated clock); "
                           "use SystemApp__wait_for_notification(timeout=...) to wait")
    tm = types.ModuleType("time"); tm.__dict__.update({k: v for k, v in vars(_time).items() if not k.startswith("__")})
    tm.time = lambda: float(clock()); tm.time_ns = lambda: int(clock() * 1e9)
    tm.monotonic = tm.perf_counter = tm.time; tm.monotonic_ns = tm.perf_counter_ns = tm.time_ns
    tm.gmtime = lambda secs=None: _time.gmtime(clock() if secs is None else secs)
    tm.localtime = tm.gmtime
    tm.ctime = lambda secs=None: _time.asctime(_time.gmtime(clock() if secs is None else secs))
    tm.asctime = lambda t=None: _time.asctime(_time.gmtime(clock()) if t is None else t)
    tm.strftime = lambda fmt, t=None: _time.strftime(fmt, _time.gmtime(clock()) if t is None else t)
    tm.sleep = sleep
    return {"time": tm, "datetime": dtm}


def _disabled(name):
    def f(*a, **k): raise RuntimeError(f"{name}() is disabled in this environment")
    f.__name__ = name
    return f


class CodeExecutor:
    """persistent python namespace; tools are plain functions named by public name. run(code) -> (output, info)."""

    def __init__(self, tools, cell_timeout_s=30, hidden=None, clock=None):
        """clock: callable -> virtual epoch seconds; if given, `import time` / `import datetime` in cells get clock_modules(clock)."""
        hidden = set(hidden or ())
        self.tools = {tool_name(t): t for t in tools if tool_name(t) not in hidden}
        self.cell_timeout_s = cell_timeout_s; self.n_cells = 0
        self._calls = []; self._writes = 0
        bi = dict(vars(builtins))
        for n in ("input", "exit", "quit", "open"): bi[n] = _disabled(n)
        bi["help"] = self._help
        if clock is not None:
            shims, real_import = clock_modules(clock), builtins.__import__
            def _import(name, globals=None, locals=None, fromlist=(), level=0):
                if level == 0 and name in shims: return shims[name]
                return real_import(name, globals, locals, fromlist, level)
            bi["__import__"] = _import
        self.ns = {"__builtins__": bi, "__name__": "__main__"}
        for n, t in self.tools.items(): self.ns[n] = self._wrap(n, t)

    def _wrap(self, name, tool):
        ex = self; is_write = bool(getattr(tool, "write_operation", False))
        def call(*args, **kwargs):
            ex._calls.append(name)
            if is_write: ex._writes += 1
            try: return tool(*args, **kwargs)
            except TypeError as e:
                if not hasattr(e, "_g2_tool"): e._g2_tool = name   # innermost tool wins
                raise
        call.__name__ = call.__qualname__ = name; call.__doc__ = tool_doc(tool); call._g2_tool = tool
        return call

    def _help(self, obj=None):
        if obj is None:
            print("Call help(\"App__tool\") for a tool's full documentation. Available tools:\n" + format_tool_index(self.tools.values())); return
        t = getattr(obj, "_g2_tool", None) if callable(obj) else None
        if t is None and isinstance(obj, str):
            t = self.tools.get(obj.strip())
            if t is None:
                app = [x for x in self.tools.values() if tool_app(x) == obj.strip()]
                if app: print(format_tool_index(app)); return
                close = difflib.get_close_matches(obj.strip(), list(self.tools), n=5, cutoff=0.5)
                print(f"No tool named {obj!r}." + (f" Similar: {', '.join(close)}" if close else "")); return
        if t is not None: print(tool_doc(t)); return
        import pydoc
        print(pydoc.render_doc(obj, renderer=pydoc.plaintext)[:4000])

    def _alarm(self, signum, frame):
        raise CellTimeout(f"cell exceeded the {self.cell_timeout_s} s time limit")

    def run(self, code):
        self.n_cells += 1; fname = f"<cell {self.n_cells}>"
        self._calls = []; self._writes = 0
        linecache.cache[fname] = (len(code), None, code.splitlines(True), fname)   # source lines in tracebacks
        buf = io.StringIO(); exc = None; err_text = ""
        use_alarm = bool(self.cell_timeout_s) and hasattr(signal, "setitimer") and threading.current_thread() is threading.main_thread()
        old = None
        try:
            if use_alarm:
                old = signal.signal(signal.SIGALRM, self._alarm); signal.setitimer(signal.ITIMER_REAL, float(self.cell_timeout_s))
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                tree = ast.parse(code, fname)
                last = tree.body.pop() if tree.body and isinstance(tree.body[-1], ast.Expr) else None
                exec(compile(tree, fname, "exec"), self.ns)
                if last is not None:
                    v = eval(compile(ast.Expression(last.value), fname, "eval"), self.ns)
                    if v is not None: print(repr(v))
        except KeyboardInterrupt:
            raise
        except BaseException as e:   # incl. SystemExit / CellTimeout
            if use_alarm: signal.setitimer(signal.ITIMER_REAL, 0)   # no late alarm while formatting
            exc, err_text = self._format_exc(e, fname)
        finally:
            if use_alarm:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old if old is not None else signal.SIG_DFL)
        printed = buf.getvalue()
        if exc is None: out = printed
        else: out = err_text + (f"\n[harness] output printed before the error:\n{printed}" if printed.strip() else "")
        return out.rstrip("\n"), {"calls": list(self._calls), "writes": self._writes, "exc": exc}

    def _format_exc(self, e, fname):
        if isinstance(e, SyntaxError):   # compile-time: no frames
            frames, only = [], traceback.format_exception_only(type(e), e)
        else:   # keep only frames of model code (<cell N>, incl. functions defined in earlier cells); drop harness and ARE internals
            frames = [f for f in traceback.extract_tb(e.__traceback__) if f.filename.startswith("<cell ")]
            only = traceback.format_exception_only(type(e), e)
        text = "Execution failed. Traceback (most recent call last):\n" + "".join(traceback.format_list(frames)) + "".join(only)
        text = text.rstrip("\n")
        name = getattr(e, "_g2_tool", None)
        if isinstance(e, TypeError) and name in self.tools:
            text += f"\n[harness] Signature (* = required): {tool_sig(self.tools[name])}"
        return (only[-1].strip() if only else type(e).__name__), text


# ---------------------------------------------------------------- selftest
def _selftest():
    from types import SimpleNamespace as NS
    import time as _time

    class FakeTool:   # duck-typed AppTool
        def __init__(self, app, fn, desc, args, ret=None, write=None, **extra):
            self.app_name = app; self.name = f"{app}__{fn.__name__}"; self._public_name = self.name; self.function = fn
            self.function_description = desc; self.args = args; self.return_type = ret; self.write_operation = write
            for k, v in extra.items(): setattr(self, k, v)
        def __call__(self, *a, **k): return self.function(*a, **k)

    class BareTool:   # minimal: only name + __call__ (graceful fallback)
        name = "Misc__ping"
        def __call__(self): return "pong"

    A = lambda n, t, d=None, **kw: NS(name=n, arg_type=t, description=d, has_default="default" in kw, default=kw.get("default"))
    sent = []
    def send_email(to, subject, body=""): sent.append((to, subject, body)); return f"email-{len(sent)}"
    def list_emails(limit=3): return [f"mail{i}" for i in range(limit)]
    def get_email(email_id): raise ValueError(f"Email {email_id} not found")
    def get_all_messages(): return []
    def sleep(seconds): _time.sleep(seconds); return "slept"
    tools = [FakeTool("Emails", send_email, "Send an email.\nThe body may be empty and the long description continues for quite a while beyond ninety characters.",
                      [A("to", "str", "recipient"), A("subject", "str", "subject line"), A("body", "str", "text", default="")], ret="str", write=True,
                      return_description="the email id"),
             FakeTool("Emails", list_emails, "List the latest emails.", [A("limit", "int", "how many", default=3)], ret=list, write=False),
             FakeTool("Emails", get_email, "Get one email.", [A("email_id", "str", "id")], ret="dict", write=False),
             FakeTool("AgentUserInterface", get_all_messages, "Hidden.", [], ret="list", write=False),
             FakeTool("Slow", sleep, "Sleep.", [A("seconds", "float")], ret="str", write=False),
             BareTool()]
    hidden = ["AgentUserInterface__get_all_messages"]
    ok = 0
    def check(cond, label, detail=""):
        nonlocal ok
        if not cond: print(f"FAIL {label}\n{detail}"); sys.exit(1)
        ok += 1; print(f"ok   {label}")

    # think stripping
    check(strip_think("<think>plan</think>\nanswer") == ("answer", "plan"), "strip_think closed")
    check(strip_think("plan only</think> answer") == ("answer", "plan only"), "strip_think template-opened think")
    check(strip_think("<think>still thinking ```python\nx=1") == ("", "<think>still thinking ```python\nx=1"), "strip_think unterminated -> ('', text)")
    check(strip_think("plain answer") == ("plain answer", ""), "strip_think no think")
    check(strip_think("<think>a</think><think>b</think>final")[0] == "final", "strip_think last </think>")
    # extraction / validation
    r = "draft:\n```python\nx = 1\n```\nfinal:\n```python\nprint(2)\n```\n"
    check(extract_code(r) == "print(2)", "extract_code last block")
    check(extract_code("```python\nprint(3)\n") == "print(3)", "extract_code unclosed fence")
    check(extract_code("no code") == "", "extract_code none")
    check(validate_code("") != "" and "SyntaxError" in validate_code("def f(:") and "placeholder" in validate_code("f(...)") and validate_code("x=1") == "",
          "validate_code")
    # readonly
    wn = {t.name for t in tools if getattr(t, "write_operation", False)}
    check(readonly("print(Emails__list_emails())", wn) and not readonly("f = Emails__send_email\nf(to='a', subject='b')", wn), "readonly")
    # index
    idx = format_tool_index(tools, hidden=hidden)
    print(idx)
    check("## Emails" in idx and "Emails__send_email(to:str*, subject:str*, body:str='') -> str  # Send an email. The body" in idx, "index line format")
    check("Emails__list_emails(limit:int=3) -> list  # List the latest emails." in idx, "index default + type object return")
    check("get_all_messages" not in idx and "AgentUserInterface" not in idx, "index excludes hidden tools")
    check("Misc__ping()" in idx, "index bare tool fallback")
    check(max(len(l.split("  # ", 1)[1]) for l in idx.splitlines() if "  # " in l) <= 90, "index desc <= 90 chars")
    # executor
    ex = CodeExecutor(tools, cell_timeout_s=1, hidden=hidden)
    out, info = ex.run("x = Emails__list_emails(limit=2)\nprint(len(x))")
    check(out == "2" and info == {"calls": ["Emails__list_emails"], "writes": 0, "exc": None}, "stdout capture + call tracking", (out, info))
    out, info = ex.run("x")
    check(out == "['mail0', 'mail1']", "persistent variable + last-expression echo", out)
    out, info = ex.run("y = 5\ny * 2")
    check(out == "10", "echo after statements", out)
    out, info = ex.run("Emails__send_email(to='a@b.c', subject='hi')")
    check(out == "'email-1'" and info["writes"] == 1 and info["calls"] == ["Emails__send_email"], "write counted + echo", (out, info))
    out, info = ex.run("print('before')\nEmails__send_email(to='a', subj='x')")
    print(out)
    check(out.startswith("Execution failed. Traceback (most recent call last):\n") and "TypeError: " in out, "exception prefix", out)
    check("\n[harness] Signature (* = required): Emails__send_email(to:str*, subject:str*, body:str='') -> str" in out, "signature hint on bad kwarg", out)
    check('File "<cell ' in out and "g2_exec.py" not in out and "subj='x'" in out, "harness frames trimmed, cell line shown", out)
    check(out.rstrip().endswith("before") and info["exc"].startswith("TypeError") and info["writes"] == 1, "prior output kept + info.exc", (out, info))
    out, info = ex.run("1 + 'a'")
    check(out.startswith("Execution failed") and "[harness] Signature" not in out, "no signature hint for non-tool TypeError", out)
    out, info = ex.run("def g(i):\n    return Emails__get_email(email_id=i)\n")
    out, info = ex.run("g('e9')")
    check(out.startswith("Execution failed") and out.count('File "<cell ') == 2 and out.endswith("ValueError: Email e9 not found"),
          "tool exception through earlier-cell function", out)
    out, info = ex.run('help("Emails__send_email")')
    print(out)
    check(out.startswith("Emails__send_email(to:str*") and "long description continues" in out and "body (str, optional, default '')" in out
          and "Returns: str -- the email id" in out and "Write operation: yes" in out and info["calls"] == [], "help full description", out)
    out, _ = ex.run("help(Emails__list_emails)")
    check(out.startswith("Emails__list_emails(limit:int=3) -> list"), "help on function object", out)
    out, _ = ex.run('help("Emails__send_mail")')
    check("No tool named" in out and "Emails__send_email" in out, "help unknown name suggests", out)
    out, _ = ex.run('help("AgentUserInterface__get_all_messages")')
    check("No tool named" in out, "hidden tool not bound", out)
    out, _ = ex.run("Misc__ping()")
    check(out == "'pong'", "bare tool callable", out)
    for n in ("input('x')", "open('f.txt')", "exit()", "quit()"):
        out, _ = ex.run(n)
        check(out.startswith("Execution failed") and "is disabled" in out, f"{n.split('(')[0]} disabled", out)
    out, _ = ex.run("raise SystemExit(3)")
    check(out.startswith("Execution failed") and "SystemExit" in out, "SystemExit caught", out)
    out, _ = ex.run("x = (")
    check(out.startswith("Execution failed. Traceback") and "SyntaxError" in out, "syntax error formatted", out)
    out, _ = ex.run("print(y)")
    check(out == "5", "namespace survives errors", out)
    if hasattr(signal, "setitimer"):
        t0 = _time.time(); out, info = ex.run("while True:\n    pass")
        check(out.startswith("Execution failed") and "CellTimeout" in out and _time.time() - t0 < 3, "cell timeout (POSIX)", out)
        out, _ = ex.run("print('alive')")
        check(out == "alive", "executor usable after timeout", out)
    else:
        print("skip cell timeout (no signal.setitimer on this platform)")
    print(f"selftest passed ({ok} checks)")


if __name__ == "__main__":
    if "--selftest" in sys.argv: _selftest()
    else: print(__doc__)
