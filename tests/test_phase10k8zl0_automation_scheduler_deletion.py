from __future__ import annotations

import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELETED = [
    'automation_scheduler/baseball_impact_common.py',
    'automation_scheduler/basketball_lineup_matchup_context.py',
    'automation_scheduler/basketball_market_relevance.py',
    'automation_scheduler/basketball_player_impact_common.py',
    'automation_scheduler/basketball_player_impact_red_team.py',
    'automation_scheduler/combat_impact_common.py',
    'automation_scheduler/correlation_structure_diagnostics.py',
    'automation_scheduler/cross_asset_embedding_router.py',
    'automation_scheduler/deepseek_prompt_contracts.py',
    'automation_scheduler/deepseek_response_validator.py',
    'automation_scheduler/extreme_signal_red_team.py',
    'automation_scheduler/football_impact_common.py',
    'automation_scheduler/football_impact_red_team.py',
    'automation_scheduler/football_impact_schema.py',
    'automation_scheduler/golf_impact_common.py',
    'automation_scheduler/hockey_impact_common.py',
    'automation_scheduler/manifold_review_queue.py',
    'automation_scheduler/market_state_graph.py',
    'automation_scheduler/prediction_market_manifold_mapper.py',
    'automation_scheduler/security_readiness_report.py',
    'automation_scheduler/soccer_impact_common.py',
    'automation_scheduler/strategy_readiness_report.py',
    'automation_scheduler/tennis_impact_common.py',
]


def test_phase10k8zl0_deleted_files_and_post_delete_docs() -> None:
    docs = [
        ROOT / 'PHASE10K8ZL0_AUTOMATION_SCHEDULER_DELETION.md',
        ROOT / 'AUTOMATION_SCHEDULER_DELETION_PROOF_AFTER_10K8ZL0.md',
        ROOT / 'POST_AUTOMATION_SCHEDULER_DELETION_IMPORT_SCAN_AFTER_10K8ZL0.md',
        ROOT / 'AUTOMATION_SCHEDULER_DELETION_COMPLETION_STATUS_AFTER_10K8ZL0.md',
        ROOT / 'REMAINING_AUTOMATION_SCHEDULER_BLOCKERS_AFTER_10K8ZL0.md',
    ]
    for path in docs:
        assert path.is_file(), path
    text = '\n'.join(path.read_text(encoding='utf-8') for path in docs)
    assert 'No deletion occurred in this batch.' in text
    assert 'Deleted files: 0' in text
    assert 'Remaining delete-ready files: 23' in text
    assert 'blocked' in text.lower()
    for rel in DELETED:
        assert (ROOT / rel).exists(), rel
    for rel in [
        'main.py', 'streamlit_app.py', 'src/services/execution_service.py', 'src/services/ledger_service.py', 'src/services/settlement_service.py',
    ]:
        assert (ROOT / rel).exists(), rel
    for mod in ['src.core.backtester', 'src.analytics', 'src.backtesting', 'src.research', 'src.brokerage']:
        importlib.import_module(mod)
