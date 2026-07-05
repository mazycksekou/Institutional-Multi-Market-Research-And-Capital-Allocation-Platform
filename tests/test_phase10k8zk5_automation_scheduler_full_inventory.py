from __future__ import annotations

import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase10k8zk5_inventory_docs_and_counts() -> None:
    docs = [
        ROOT / 'PHASE10K8ZK5_AUTOMATION_SCHEDULER_FULL_INVENTORY.md',
        ROOT / 'AUTOMATION_SCHEDULER_FILE_INVENTORY_AFTER_10K8ZK5.md',
        ROOT / 'AUTOMATION_SCHEDULER_OWNERSHIP_CLASSIFICATION_AFTER_10K8ZK5.md',
        ROOT / 'AUTOMATION_SCHEDULER_IMPORT_SCAN_AFTER_10K8ZK5.md',
        ROOT / 'AUTOMATION_SCHEDULER_TEST_SCAN_AFTER_10K8ZK5.md',
        ROOT / 'AUTOMATION_SCHEDULER_DECOMMISSION_QUEUE_AFTER_10K8ZK5.md',
    ]
    for path in docs:
        assert path.is_file(), path

    text = '\n'.join(path.read_text(encoding='utf-8') for path in docs)
    for phrase in [
        'Canonical src.* architecture already exists',
        'Delete-ready after proof',
        'MIGRATE_TO_SRC_CORE',
        'MIGRATE_TO_SRC_SERVICES',
        'MIGRATE_TO_SRC_DATA',
        'MIGRATE_TO_SRC_BACKTESTING',
        'MIGRATE_TO_SRC_ANALYTICS',
        'MIGRATE_TO_SRC_RESEARCH',
        'MIGRATE_TO_SRC_AI',
        'MIGRATE_TO_SRC_BROKERAGE',
        'MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER',
        'COMPATIBILITY_WRAPPER_ONLY',
        'DELETE_READY_AFTER_PROOF',
        'live trading',
        'credential reads',
        'broker SDK',
    ]:
        assert phrase in text

    assert text.count('automation_scheduler/') >= 300

    for mod in ['src.core.backtester', 'src.analytics', 'src.backtesting', 'src.research', 'src.brokerage']:
        importlib.import_module(mod)
