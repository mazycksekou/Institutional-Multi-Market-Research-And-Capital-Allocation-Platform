from live_market_intelligence.replay.replay_engine import run_replay


def test_replay_engine_runs_synthetic_replay_without_execution():
    result = run_replay()
    assert result["ok"] is True
    assert result["execution_allowed"] is False
    assert result["alerts"]
