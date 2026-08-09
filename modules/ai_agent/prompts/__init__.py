from __future__ import annotations

from pathlib import Path

_PROMPT_DIR = Path(__file__).parent


def load_prompt(name: str, **kwargs) -> str:
    text = (_PROMPT_DIR / f"{name}.txt").read_text(encoding="utf-8")
    if kwargs:
        text = text.format(**kwargs)
    return text
