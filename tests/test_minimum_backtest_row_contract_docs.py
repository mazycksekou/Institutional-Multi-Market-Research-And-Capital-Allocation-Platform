from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_minimum_backtest_row_contract_docs_exist_and_cover_required_topics() -> None:
    minimum_contract = DOCS / "contracts" / "MINIMUM_BACKTEST_ROW_CONTRACT.md"
    nfl_contract = DOCS / "contracts" / "NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md"
    readiness_checklist = DOCS / "reports" / "NFL_BACKTEST_ROW_READINESS_CHECKLIST.md"
    alignment_rules = DOCS / "reports" / "NFL_DECISION_TIME_ALIGNMENT_RULES.md"
    exclusion_rules = DOCS / "reports" / "NFL_BACKTEST_ROW_EXCLUSION_RULES.md"
    streamlit_spec = DOCS / "reports" / "NFL_STREAMLIT_BACKTEST_READINESS_SPEC.md"
    worldview_spec = DOCS / "reports" / "NFL_WORLDVIEW_BACKTEST_READINESS_SPEC.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"

    for path in [
        minimum_contract,
        nfl_contract,
        readiness_checklist,
        alignment_rules,
        exclusion_rules,
        streamlit_spec,
        worldview_spec,
        project_status,
        next_action,
    ]:
        assert path.exists(), f"missing document: {path}"

    minimum_contract_text = _read(minimum_contract)
    nfl_contract_text = _read(nfl_contract)
    readiness_checklist_text = _read(readiness_checklist)
    alignment_rules_text = _read(alignment_rules)
    exclusion_rules_text = _read(exclusion_rules)
    streamlit_spec_text = _read(streamlit_spec)
    worldview_spec_text = _read(worldview_spec)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)

    # Generic reusable contract
    assert "Minimum Backtest Row Contract" in minimum_contract_text
    assert "Sports" in minimum_contract_text
    assert "Prediction Markets" in minimum_contract_text
    assert "Options / 0DTE" in minimum_contract_text
    assert "required identifiers" in minimum_contract_text.lower()
    assert "market_profile" in minimum_contract_text
    assert "profile_family" in minimum_contract_text
    assert "season" in minimum_contract_text.lower()
    assert "event_or_contract_id" in minimum_contract_text
    assert "decision_time" in minimum_contract_text
    assert "odds_snapshot_time" in minimum_contract_text
    assert "feature_snapshot_time" in minimum_contract_text
    assert "event_start_time" in minimum_contract_text
    assert "result_recorded_time" in minimum_contract_text
    assert "point-in-time" in minimum_contract_text.lower()
    assert "leakage" in minimum_contract_text.lower()
    assert "BACKTEST_ELIGIBLE" in minimum_contract_text
    assert "NO_TRADE" in minimum_contract_text
    assert "EXCLUDED" in minimum_contract_text
    assert "NEEDS_REVIEW" in minimum_contract_text
    assert "minimum ready" in minimum_contract_text.lower()
    assert "research ready" in minimum_contract_text.lower()
    assert "strong ready" in minimum_contract_text.lower()
    assert "production candidate ready" in minimum_contract_text.lower()
    assert "Worldview" in minimum_contract_text

    # NFL instantiation
    assert "sports:nfl" in nfl_contract_text
    assert "13/13" in nfl_contract_text
    assert "2 full regular seasons" in nfl_contract_text
    assert "400 resolved decision rows" in nfl_contract_text
    assert "decision_time" in nfl_contract_text
    assert "point-in-time" in nfl_contract_text.lower()
    assert "no unresolved leakage violation" in nfl_contract_text.lower()
    assert "minimum readiness" in nfl_contract_text.lower()
    assert "Streamlit" in nfl_contract_text
    assert "Worldview" in nfl_contract_text

    # Supportive reports
    assert "backtest-ready" in readiness_checklist_text.lower()
    assert "decision_time" in alignment_rules_text
    assert "at or before" in alignment_rules_text.lower()
    assert "missing odds snapshot" in exclusion_rules_text.lower()
    assert "no_trade" in exclusion_rules_text.lower()
    assert "readiness" in streamlit_spec_text.lower()
    assert "backtest-ready" in streamlit_spec_text.lower()
    assert "Worldview" in worldview_spec_text
    assert "evidence package" in worldview_spec_text.lower()

    # Project status / next action wiring
    assert "Phase 4.5E - Canonical Engineering Specification Rename & Research Asset Runtime Framework" in project_status_text
    assert "master research engine specification" in project_status_text.lower()
    assert "Phase 4.8 - Historical Feature Population" in next_action_text
    assert "minimum certified schema first" in next_action_text.lower()
    assert "validation commands" in next_action_text.lower()


def test_minimum_backtest_row_contract_docs_do_not_depend_on_runtime_code() -> None:
    minimum_contract = DOCS / "contracts" / "MINIMUM_BACKTEST_ROW_CONTRACT.md"
    nfl_contract = DOCS / "contracts" / "NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md"

    for text in (_read(minimum_contract), _read(nfl_contract)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "contract" in text.lower()
