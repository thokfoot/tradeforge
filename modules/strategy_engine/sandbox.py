from __future__ import annotations

import ast
import base64
import pickle
import subprocess
import sys
from textwrap import dedent

ALLOWED_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "divmod": divmod,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "isinstance": isinstance,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "pow": pow,
    "range": range,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}

BLOCKED_NAMES = {
    "eval",
    "exec",
    "compile",
    "open",
    "input",
    "breakpoint",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
    "__import__",
    "type",
    "help",
    "print",
}

BLOCKED_ATTRS = {
    "read_csv",
    "read_parquet",
    "read_json",
    "read_excel",
    "read_html",
    "to_csv",
    "to_parquet",
    "to_json",
    "to_excel",
    "to_pickle",
    "to_sql",
    "system",
    "popen",
    "check_output",
    "getoutput",
    "call",
    "urlopen",
    "connect",
    "socket",
    "startfile",
}

_WORKER = dedent(
    """
    import base64
    import pickle
    import sys
    try:
        import resource
    except ImportError:
        resource = None

    def _run():
        payload = pickle.loads(base64.b64decode(sys.stdin.buffer.read()))
        if resource is not None:
            try:
                resource.setrlimit(resource.RLIMIT_CPU, (payload["cpu"], payload["cpu"]))
                resource.setrlimit(resource.RLIMIT_AS, (payload["mem"], payload["mem"]))
            except Exception:
                pass
        import numpy as np
        import pandas as pd
        restricted = {
            "__builtins__": payload["builtins"],
            "__name__": "__sandbox__",
            "np": np,
            "pd": pd,
            "data": payload["data"],
            "params": payload["params"],
        }
        result = {}
        error = None
        try:
            exec(compile(payload["code"], "<strategy>", "exec"), restricted, result)
        except BaseException as exc:
            error = exc
        out = {"result": result, "error": error}
        sys.stdout.buffer.write(b"TF_RESULT:" + base64.b64encode(pickle.dumps(out)))
        sys.stdout.buffer.flush()

    _run()
    """
)


def _ast_check(code: str) -> None:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise NameError("imports are not allowed in strategy code")
        if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES and isinstance(node.ctx, ast.Load):
            raise NameError(f"{node.id} is not allowed in strategy code")
        if isinstance(node, ast.Attribute):
            if "__" in node.attr:
                raise NameError("access to protected attributes is not allowed")
            if node.attr in BLOCKED_ATTRS:
                raise NameError(f"{node.attr} is not allowed in strategy code")


def run_code(
    code: str,
    namespace: dict,
    timeout: float = 2.0,
    cpu_limit: int = 20,
    mem_limit: int = 1_600_000_000,
) -> dict:
    """Execute untrusted strategy code in an isolated worker process.

    Returns the globals written by the code (e.g. ``signals``). Any error the
    code raises is re-raised in the caller. Disallowed constructs are rejected
    up front via an AST gate; CPU, wall-clock and memory are bounded in the
    worker so a runaway strategy cannot take the server down.
    """
    _ast_check(code)
    payload = base64.b64encode(
        pickle.dumps(
            {
                "code": code,
                "builtins": ALLOWED_BUILTINS,
                "data": namespace.get("data"),
                "params": namespace.get("params", {}),
                "cpu": int(cpu_limit),
                "mem": int(mem_limit),
            }
        )
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _WORKER],
            input=payload,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("strategy code timed out") from None
    marker = b"TF_RESULT:"
    if not proc.stdout.startswith(marker):
        raise RuntimeError("strategy sandbox failed to produce a result")
    decoded = pickle.loads(base64.b64decode(proc.stdout[len(marker):].strip()))
    if decoded.get("error") is not None:
        raise decoded["error"]
    return decoded.get("result", {})
