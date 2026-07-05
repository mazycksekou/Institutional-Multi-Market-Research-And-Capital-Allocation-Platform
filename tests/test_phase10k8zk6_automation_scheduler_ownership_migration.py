from __future__ import annotations

import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase10k8zk6_migration_map_mentions_canonical_targets() -> None:
    docs = [
        ROOT / 'PHASE10K8ZK6_AUTOMATION_SCHEDULER_OWNERSHIP_MIGRATION.md',
        ROOT / 'AUTOMATION_SCHEDULER_MIGRATION_MAP_AFTER_10K8ZK6.md',
        ROOT / 'AUTOMATION_SCHEDULER_CANONICAL_TARGETS_AFTER_10K8ZK6.md',
        ROOT / 'AUTOMATION_SCHEDULER_COMPATIBILITY_REPORT_AFTER_10K8ZK6.md',
    ]
    for path in docs:
        assert path.is_file(), path
    text = '\n'.join(path.read_text(encoding='utf-8') for path in docs)
    for phrase in [
        'src.core', 'src.services', 'src.data', 'src.backtesting', 'src.analytics', 'src.research', 'src.ai', 'src.brokerage',
        'MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER', 'COMPATIBILITY_WRAPPER_ONLY', 'Delete-ready files remain',
    ]:
        assert phrase in text
    for mod in ['src.data', 'src.backtesting', 'src.analytics', 'src.research', 'src.ai', 'src.brokerage']:
        importlib.import_module(mod)
