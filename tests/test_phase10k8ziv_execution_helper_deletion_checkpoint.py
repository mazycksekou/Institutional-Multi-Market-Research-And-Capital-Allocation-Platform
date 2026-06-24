from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIV_EXECUTION_HELPER_DELETION_CHECKPOINT.md",
    ROOT / "POST_EXECUTION_HELPER_DELETION_ARCHITECTURE_MAP_AFTER_10K8ZIV.md",
    ROOT / "REMAINING_EXECUTION_HELPER_BLOCKERS_AFTER_10K8ZIV.md",
    ROOT / "NEXT_LIVE_TRADING_PREP_PLAN_AFTER_10K8ZIV.md",
]


def test_deletion_checkpoint_docs_exist() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "Runtime helper ownership is canonical in `src.services` and `src.brokerage`.",
        "The nine wrapper-only execution helpers were deleted after proof.",
        "Canonical execution path:",
        "Next Live Trading Prep Plan",
    ]:
        assert fragment in text
