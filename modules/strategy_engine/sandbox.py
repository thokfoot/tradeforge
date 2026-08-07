from __future__ import annotations

import threading

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
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "pow": pow,
    "range": range,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}


def run_code(code: str, namespace: dict, timeout: float = 2.0) -> dict:
    restricted: dict = {
        "__builtins__": ALLOWED_BUILTINS,
        "__name__": "__sandbox__",
    }
    restricted.update(namespace)
    result: dict = {}

    def _exec() -> None:
        try:
            exec(compile(code, "<strategy>", "exec"), restricted, result)
        except BaseException as exc:  # noqa: BLE001 - surfaced to caller
            result["__error__"] = exc

    thread = threading.Thread(target=_exec, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError("strategy code timed out")
    if "__error__" in result:
        raise result["__error__"]
    return result
