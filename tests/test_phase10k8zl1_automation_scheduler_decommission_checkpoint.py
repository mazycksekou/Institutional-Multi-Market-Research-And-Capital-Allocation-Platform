from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase10k8zl1_checkpoint_docs_reflect_partial_decommission() -> None:
    docs = [
        ROOT / 'PHASE10K8ZL1_AUTOMATION_SCHEDULER_DECOMMISSION_CHECKPOINT.md',
        ROOT / 'POST_AUTOMATION_SCHEDULER_ARCHITECTURE_MAP_AFTER_10K8ZL1.md',
        ROOT / 'FINAL_AUTOMATION_SCHEDULER_STATUS_AFTER_10K8ZL1.md',
        ROOT / 'NEXT_MARKET_INTELLIGENCE_REPO_INVENTORY_PLAN_AFTER_10K8ZL1.md',
    ]
    for path in docs:
        assert path.is_file(), path
    text = '\n'.join(path.read_text(encoding='utf-8') for path in docs)
    assert 'Deleted files: 0' in text
    assert 'Remaining files: 329' in text
    assert 'blocked' in text.lower() or 'partially decommissioned' in text.lower()
    assert 'market-intelligence' in text.lower()
    assert 'src.core' in text and 'src.brokerage' in text
