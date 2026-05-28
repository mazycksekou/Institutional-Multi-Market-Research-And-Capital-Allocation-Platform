from __future__ import annotations

import re
from typing import Any

SCHEMA_VERSION = "model_governance.v1"
BANNED_OUTPUT_TERMS = ("lock", "guaranteed", "risk-free", "sure thing", "can't lose", "cant lose")


def contains_banned_language(value: Any) -> bool:
    rendered = repr(value).lower().replace("\u2019", "'")
    return any(re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", rendered) for term in BANNED_OUTPUT_TERMS)


def safe_decision_label(value: str) -> str:
    if contains_banned_language(value):
        return "blocked_by_governance"
    return value

