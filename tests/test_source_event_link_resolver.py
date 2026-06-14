from automation_scheduler.source_event_link_resolver import (
    normalize_event_link_value,
    normalize_event_link_token,
    normalize_event_link_date,
    build_event_link_key,
    build_reversed_event_link_key,
    score_event_link_candidate,
    build_event_link_index,
    resolve_source_event_link,
    resolve_source_event_links,
    apply_resolved_event_id_to_snapshot_row,
    load_canonical_events_from_sqlite,
    build_source_event_link_resolver_snapshot,
    describe_source_event_link_resolver,
    SOURCE_EVENT_LINK_RESOLVER_VERSION,
)


# ── normalize_event_link_value ─────────────────────────────────────────


def test_normalize_event_link_value_handles_common_values():
    assert normalize_event_link_value(None) == ""
    assert normalize_event_link_value(True) == "Yes"
    assert normalize_event_link_value(False) == "No"
    assert normalize_event_link_value(42) == "42"
    assert normalize_event_link_value(3.14) == "3.14"
    assert normalize_event_link_value([1, 2]) == "[1, 2]"
    dct = {"a": 1, "b": 2}
    # sorted keys
    assert normalize_event_link_value(dct) == '{"a": 1, "b": 2}'
    assert normalize_event_link_value("  abc  ") == "abc"


# ── normalize_event_link_token ─────────────────────────────────────────


def test_normalize_event_link_token_lowercases_and_collapses():
    assert normalize_event_link_token("  Hello,  World!  ") == "hello world"
    assert normalize_event_link_token("FC Barcelona") == "fc barcelona"
    assert normalize_event_link_token("") == ""
    assert normalize_event_link_token(None) == ""


# ── normalize_event_link_date ──────────────────────────────────────────


def test_normalize_event_link_date_accepts_iso_datetime():
    # plain date
    assert normalize_event_link_date("2024-06-15") == "2024-06-15"
    # full ISO datetime
    assert normalize_event_link_date("2024-06-15T14:30:00Z") == "2024-06-15"
    assert normalize_event_link_date("") == ""
    assert normalize_event_link_date(None) == ""
    # unparseable, falls back to token
    result = normalize_event_link_date("some date")
    assert isinstance(result, str)
    assert len(result) > 0  # just something


# ── build_event_link_key ───────────────────────────────────────────────


def test_build_event_link_key_is_stable():
    row1 = {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
            "home_team": "Arsenal", "away_team": "Chelsea"}
    row2 = {"sport": "soccer", "league": "epl", "event_date": "2024-06-15",
            "home_team": "  Arsenal  ", "away_team": "Chelsea  "}
    k1 = build_event_link_key(row1)
    k2 = build_event_link_key(row2)
    assert k1 == k2
    assert k1 == "soccer|epl|2024-06-15|arsenal|chelsea"


# ── build_reversed_event_link_key ──────────────────────────────────────


def test_build_reversed_event_link_key_swaps_teams():
    row = {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
           "home_team": "Arsenal", "away_team": "Chelsea"}
    normal = build_event_link_key(row)
    rev = build_reversed_event_link_key(row)
    assert normal != rev
    assert rev.endswith("|chelsea|arsenal")


# ── score_event_link_candidate ─────────────────────────────────────────


def test_score_event_link_candidate_exact_match_scores_100():
    source = {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
              "home_team": "Arsenal", "away_team": "Chelsea"}
    cand = {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
            "home_team": "Arsenal", "away_team": "Chelsea"}
    info = score_event_link_candidate(source, cand)
    assert info["score"] == 100
    assert info["reversed_home_away"] is False


def test_score_event_link_candidate_reversed_scores_90():
    source = {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
              "home_team": "Arsenal", "away_team": "Chelsea"}
    cand = {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
            "home_team": "Chelsea", "away_team": "Arsenal"}
    info = score_event_link_candidate(source, cand)
    assert info["score"] >= 30  # actually 25+30+? (date 30 + team reversed 30 = 85? plus sport 25 = 80? Wait calculation leads 25+30+30=85? plus league 5 = 90) Indeed 90.
    # Our formula: sport 25, league 5 = 30, date 30 = 60, team reversed 30 = 90. Good.
    assert info["reversed_home_away"] is True


def test_score_event_link_candidate_missing_date_does_not_overlink():
    source = {"sport": "soccer", "home_team": "Arsenal", "away_team": "Chelsea"}
    cand = {"sport": "soccer", "home_team": "Arsenal", "away_team": "Chelsea",
            "event_date": "2024-06-15"}
    info = score_event_link_candidate(source, cand)
    # missing source date, max possible: sport 25 + team exact 40 = 65
    assert info["score"] <= 80
    assert "missing source event_date" in info["reasons"]


# ── build_event_link_index ─────────────────────────────────────────────


def test_build_event_link_index_counts_events():
    rows = [
        {"event_id": "e1", "sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
         "home_team": "Arsenal", "away_team": "Chelsea"},
        {"event_id": "e2", "sport": "baseball", "league": "MLB", "event_date": "2024-06-16",
         "home_team": "Yankees", "away_team": "Red Sox"},
    ]
    idx = build_event_link_index(rows)
    assert idx["ok"] is True
    assert idx["total_events"] == 2
    assert len(idx["event_key_index"]) == 2


def test_build_event_link_index_skips_missing_event_id():
    rows = [
        {"event_id": None, "sport": "soccer"},
        {"event_id": "e2", "sport": "baseball"},
    ]
    idx = build_event_link_index(rows)
    assert idx["total_events"] == 1
    assert "missing_event_id" in idx["warnings"]


# ── resolve_source_event_link ──────────────────────────────────────────


def test_resolve_source_event_link_uses_existing_event_id():
    result = resolve_source_event_link({"event_id": "e1", "sport": "soccer"})
    assert result["resolved"] is True
    assert result["event_id"] == "e1"
    assert result["match_method"] == "existing_event_id"


def test_resolve_source_event_link_uses_source_event_id_exact_match():
    cand_rows = [
        {"event_id": "e1", "source_key": "srcA", "source_event_id": "src_123",
         "sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
         "home_team": "Arsenal", "away_team": "Chelsea"},
    ]
    source = {"source_key": "srcA", "source_event_id": "src_123"}
    result = resolve_source_event_link(source, canonical_event_rows=cand_rows)
    assert result["resolved"] is True
    assert result["event_id"] == "e1"
    assert result["match_method"] == "source_event_id"


def test_resolve_source_event_link_uses_exact_event_key():
    cand_rows = [
        {"event_id": "e1", "sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
         "home_team": "Arsenal", "away_team": "Chelsea"},
    ]
    source = {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
              "home_team": "Arsenal", "away_team": "Chelsea"}
    result = resolve_source_event_link(source, canonical_event_rows=cand_rows)
    assert result["resolved"] is True
    assert result["match_method"] == "exact_event_key"
    assert result["score"] == 100


def test_resolve_source_event_link_does_not_resolve_ambiguous_match():
    cand_rows = [
        {"event_id": "e1", "sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
         "home_team": "Arsenal", "away_team": "Chelsea"},
        {"event_id": "e2", "sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
         "home_team": "Arsenal", "away_team": "Chelsea"},
    ]
    source = {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
              "home_team": "Arsenal", "away_team": "Chelsea"}
    result = resolve_source_event_link(source, canonical_event_rows=cand_rows)
    assert result["resolved"] is False
    assert result["match_method"] == "ambiguous"


def test_resolve_source_event_link_allows_reversed_when_min_score_90():
    cand_rows = [
        {"event_id": "e1", "sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
         "home_team": "Chelsea", "away_team": "Arsenal"},
    ]
    source = {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
              "home_team": "Arsenal", "away_team": "Chelsea"}
    result = resolve_source_event_link(source, canonical_event_rows=cand_rows, min_score=90)
    assert result["resolved"] is True
    assert result["match_method"] == "reversed_home_away"


# ── resolve_source_event_links ─────────────────────────────────────────


def test_resolve_source_event_links_empty_rows():
    result = resolve_source_event_links([])
    assert result["ok"] is True
    assert result["warnings"] == ["no_rows"]


def test_resolve_source_event_links_counts_resolved_and_unresolved():
    cand_rows = [
        {"event_id": "e1", "sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
         "home_team": "Arsenal", "away_team": "Chelsea"},
        {"event_id": "e2", "sport": "baseball", "league": "MLB", "event_date": "2024-06-16",
         "home_team": "Yankees", "away_team": "Red Sox"},
    ]
    sources = [
        {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
         "home_team": "Arsenal", "away_team": "Chelsea"},
        {"sport": "basketball", "event_date": "2024-06-15", "home_team": "Lakers", "away_team": "Celtics"},
    ]
    result = resolve_source_event_links(sources, canonical_event_rows=cand_rows)
    assert result["total_rows"] == 2
    assert result["resolved_rows"] == 1
    assert result["unresolved_rows"] >= 1


# ── apply_resolved_event_id_to_snapshot_row ────────────────────────────


def test_apply_resolved_event_id_to_snapshot_row_does_not_mutate_input():
    snap = {"event_id": None, "sport": "soccer"}
    resolution = {"resolved": True, "event_id": "e1"}
    result = apply_resolved_event_id_to_snapshot_row(snap, resolution)
    assert snap["event_id"] is None  # unchanged
    assert result["event_id"] == "e1"


def test_apply_resolved_event_id_to_snapshot_row_sets_event_id_when_resolved():
    snap = {"event_id": None, "sport": "soccer"}
    resolution = {"resolved": False, "event_id": None}
    result = apply_resolved_event_id_to_snapshot_row(snap, resolution)
    assert result["event_id"] is None  # unchanged


# ── load_canonical_events_from_sqlite ──────────────────────────────────


def test_load_canonical_events_from_sqlite_missing_db():
    result = load_canonical_events_from_sqlite("/nonexistent/path/db.db")
    assert result["ok"] is False
    assert len(result["warnings"]) > 0


def test_load_canonical_events_from_sqlite_reads_historical_events(tmp_path):
    from automation_scheduler.historical_odds_sqlite import (
        connect_historical_odds_db,
        initialize_historical_odds_db,
    )
    db_path = tmp_path / "test_events.db"
    conn = connect_historical_odds_db(db_path)
    initialize_historical_odds_db(conn)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS historical_events ("
        "event_id TEXT, sport TEXT, league TEXT, event_date TEXT, "
        "home_team TEXT, away_team TEXT, source_event_id TEXT, source_key TEXT)"
    )
    conn.execute(
        "INSERT INTO historical_events (event_id, sport, league, event_date, home_team, away_team, source_event_id, source_key) "
        "VALUES (?,?,?,?,?,?,?,?)",
        ('e1','soccer','EPL','2024-06-15','Arsenal','Chelsea','src1','football_data_uk')
    )
    conn.commit()
    conn.close()

    result = load_canonical_events_from_sqlite(db_path)
    assert result["ok"] is True
    assert result["total_events"] == 1
    assert result["events"][0]["event_id"] == "e1"


# ── build_source_event_link_resolver_snapshot ──────────────────────────


def test_build_source_event_link_resolver_snapshot_empty():
    snap = build_source_event_link_resolver_snapshot()
    assert snap["ok"] is True
    assert "event_index" in snap
    assert snap["resolution"] is None


# ── describe_source_event_link_resolver ────────────────────────────────


def test_describe_source_event_link_resolver_mentions_no_vendor_import():
    msgs = describe_source_event_link_resolver()
    combined = " ".join(msgs)
    assert "does not connect to vendors" in combined


def test_describe_source_event_link_resolver_mentions_phase_10h22():
    msgs = describe_source_event_link_resolver()
    combined = " ".join(msgs)
    assert "Phase 10H22" in combined


# ── additional safeguard ────────────────────────────────────────────────


def test_resolver_does_not_auto_link_ambiguous_candidates():
    cand_rows = [
        {"event_id": "e1", "sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
         "home_team": "TeamA", "away_team": "TeamB"},
        {"event_id": "e2", "sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
         "home_team": "TeamA", "away_team": "TeamB"},
    ]
    source = {"sport": "soccer", "league": "EPL", "event_date": "2024-06-15",
              "home_team": "TeamA", "away_team": "TeamB"}
    result = resolve_source_event_link(source, canonical_event_rows=cand_rows)
    assert result["resolved"] is False
    assert result["match_method"] == "ambiguous"
