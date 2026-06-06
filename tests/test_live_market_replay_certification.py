from live_market_intelligence.replay.replay_certification import certify_replay


def test_replay_certification_passes_synthetic_fixture():
    report = certify_replay()
    assert report["ok"] is True
    assert report["replay_certification_status"] == "passed"
    assert report["actual_bets_submitted"] == 0
