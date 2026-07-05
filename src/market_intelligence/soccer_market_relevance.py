from __future__ import annotations

from typing import Any

from .soccer_impact_common import FIRST_HALF_MARKETS, PLAYER_PROP_MARKETS, REFEREE_MARKETS, SET_PIECE_MARKETS, TACTICAL_MARKETS, TEAM_MARKETS, TOTAL_MARKETS, clamp, compact_list, finalize_soccer_response, normalize_soccer_market, score_from_range, weighted_average


def _score(payload: dict[str, Any] | None, key: str) -> float:
    return clamp(payload.get(key, 0.0) or 0.0) if isinstance(payload, dict) else 0.0


def _top_links(scores: dict[str, float], threshold: float = 58.0) -> list[str]:
    return [market for market, score in sorted(scores.items(), key=lambda item: item[1], reverse=True) if score >= threshold][:12]


def evaluate_soccer_market_relevance(
    row: dict[str, Any] | None = None,
    *,
    market_type: str | None = None,
    possession_value_impact: dict[str, Any] | None = None,
    tactical_context: dict[str, Any] | None = None,
    pressing_transition_context: dict[str, Any] | None = None,
    player_role_impact: dict[str, Any] | None = None,
    lineup_availability_context: dict[str, Any] | None = None,
    set_piece_context: dict[str, Any] | None = None,
    goalkeeper_context: dict[str, Any] | None = None,
    referee_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    market = normalize_soccer_market(market_type or source.get("market_type") or "three_way_moneyline")
    possession = possession_value_impact or {}
    tactical = tactical_context or {}
    pressing = pressing_transition_context or {}
    player = player_role_impact or {}
    lineup = lineup_availability_context or {}
    set_piece = set_piece_context or {}
    keeper = goalkeeper_context or {}
    referee = referee_context or {}
    matchup = matchup_context or {}
    incentive = incentive_context or {}
    pv = _score(possession, "possession_value_score")
    chance = _score(possession, "chance_quality_score")
    territorial = _score(possession, "territorial_dominance_score")
    progression = _score(possession, "progression_score")
    xg = _score(possession, "xg_quality_score")
    first_half = _score(possession, "first_half_pressure_score")
    open_play = _score(possession, "open_play_attack_score")
    defense = _score(possession, "defensive_suppression_score")
    total_signal = _score(possession, "total_signal_score")
    team_total = _score(possession, "team_total_signal_score")
    btts = _score(possession, "btts_signal_score")
    tactical_fit = _score(tactical, "tactical_fit_score")
    tactical_risk = _score(tactical, "tactical_mismatch_risk")
    press_score = _score(pressing, "pressing_impact_score")
    transition_attack = _score(pressing, "transition_attack_score")
    transition_risk = _score(pressing, "transition_defense_risk")
    player_market = _score(player, "player_market_relevance")
    attack_player = _score(player, "attacking_threat_score")
    creative = _score(player, "creative_value_score")
    defensive_work = _score(player, "defensive_work_score")
    card_risk = _score(player, "card_risk_score")
    minutes = _score(player, "minutes_role_stability_score")
    lineup_certainty = _score(lineup, "lineup_certainty_score")
    availability = _score(lineup, "availability_score")
    rotation = _score(lineup, "rotation_risk_score")
    set_piece_attack = _score(set_piece, "set_piece_attack_score")
    penalty_context = _score(set_piece, "penalty_context_score")
    set_piece_goal = _score(set_piece, "player_goal_prop_modifier")
    keeper_score = _score(keeper, "goalkeeper_impact_score")
    keeper_certainty = _score(keeper, "starter_certainty_score")
    keeper_total = _score(keeper, "total_market_goalkeeper_modifier")
    keeper_prop = _score(keeper, "goalkeeper_prop_relevance")
    ref_cards = _score(referee, "card_market_relevance")
    ref_penalty = _score(referee, "penalty_market_relevance")
    ref_fouls = _score(referee, "foul_market_relevance")
    red_vol = _score(referee, "red_card_volatility_risk")
    match_adv = _score(matchup, "matchup_advantage_score")
    match_risk = _score(matchup, "matchup_risk_score")
    modifier = incentive.get("market_relevance_modifier") if isinstance(incentive.get("market_relevance_modifier"), dict) else {}
    scores = {
        "three_way_moneyline": weighted_average(((xg, 0.35), (pv, 0.3), (lineup_certainty, 0.3), (keeper_score, 0.25), (tactical_fit, 0.2), (100.0 - match_risk, 0.15))) or 0.0,
        "moneyline": weighted_average(((xg, 0.35), (pv, 0.28), (keeper_score, 0.25), (availability, 0.25), (match_adv, 0.2))) or 0.0,
        "draw_no_bet": weighted_average(((xg, 0.35), (defense, 0.25), (keeper_score, 0.25), (100.0 - match_risk, 0.2))) or 0.0,
        "double_chance": weighted_average(((defense, 0.3), (keeper_score, 0.25), (availability, 0.2), (100.0 - match_risk, 0.25))) or 0.0,
        "asian_handicap": weighted_average(((xg, 0.35), (territorial, 0.25), (defense, 0.2), (match_adv, 0.25), (lineup_certainty, 0.2))) or 0.0,
        "spread": weighted_average(((xg, 0.35), (territorial, 0.25), (match_adv, 0.25), (100.0 - rotation, 0.15))) or 0.0,
        "total": weighted_average(((total_signal, 0.45), (transition_risk, 0.25), (set_piece_attack, 0.18), (keeper_total, 0.25), (ref_penalty, 0.15))) or 0.0,
        "team_total": weighted_average(((team_total, 0.45), (open_play, 0.3), (set_piece_attack, 0.2), (match_adv, 0.2), (100.0 - keeper_score, 0.15))) or 0.0,
        "both_teams_to_score": weighted_average(((btts, 0.45), (transition_risk, 0.3), (keeper_total, 0.2), (set_piece_attack, 0.15))) or 0.0,
        "correct_score": weighted_average(((defense, 0.25), (keeper_score, 0.25), (100.0 - total_signal, 0.2), (100.0 - red_vol, 0.3))) or 0.0,
        "first_half_moneyline": weighted_average(((first_half, 0.45), (xg, 0.25), (press_score, 0.2), (lineup_certainty, 0.15))) or 0.0,
        "first_half_total": weighted_average(((first_half, 0.55), (transition_attack, 0.2), (press_score, 0.2), (keeper_total, 0.15))) or 0.0,
        "first_half_team_total": weighted_average(((first_half, 0.45), (team_total, 0.3), (set_piece_attack, 0.15))) or 0.0,
        "first_half_asian_handicap": weighted_average(((first_half, 0.4), (xg, 0.25), (match_adv, 0.2), (lineup_certainty, 0.15))) or 0.0,
        "anytime_goal": weighted_average(((attack_player, 0.45), (set_piece_goal, 0.25), (minutes, 0.3), (penalty_context, 0.2))) or 0.0,
        "shots": weighted_average(((attack_player, 0.45), (player_market, 0.3), (minutes, 0.25), (match_adv, 0.15))) or 0.0,
        "shots_on_target": weighted_average(((attack_player, 0.45), (xg, 0.2), (minutes, 0.25), (set_piece_goal, 0.1))) or 0.0,
        "assists": weighted_average(((creative, 0.5), (progression, 0.25), (set_piece_goal, 0.15), (minutes, 0.25))) or 0.0,
        "passes": weighted_average(((creative, 0.25), (progression, 0.25), (territorial, 0.25), (minutes, 0.25))) or 0.0,
        "tackles": weighted_average(((defensive_work, 0.45), (press_score, 0.25), (transition_risk, 0.2), (minutes, 0.25))) or 0.0,
        "cards": max(
            weighted_average(((card_risk, 0.45), (ref_cards, 0.45), (match_risk, 0.2))) or 0.0,
            weighted_average(((ref_cards, 0.65), (ref_fouls, 0.2), (tactical_risk, 0.15))) or 0.0,
        ),
        "fouls_committed": max(
            weighted_average(((card_risk, 0.35), (ref_cards, 0.25), (defensive_work, 0.2), (match_risk, 0.2))) or 0.0,
            weighted_average(((ref_fouls, 0.55), (ref_cards, 0.25), (tactical_risk, 0.2))) or 0.0,
        ),
        "fouls_drawn": max(
            weighted_average(((attack_player, 0.3), (creative, 0.25), (ref_cards, 0.2), (minutes, 0.25))) or 0.0,
            weighted_average(((ref_fouls, 0.45), (attack_player, 0.25), (creative, 0.15), (minutes, 0.15))) or 0.0,
        ),
        "saves": weighted_average(((keeper_prop, 0.45), (keeper_certainty, 0.45), (score_from_range(source.get("opponent_shot_volume"), low=5, high=20) or 0.0, 0.25))) or 0.0,
        "goalkeeper_saves": weighted_average(((keeper_prop, 0.45), (keeper_certainty, 0.45), (score_from_range(source.get("opponent_xg"), low=0.4, high=2.8) or 0.0, 0.25))) or 0.0,
    }
    player_adjustment = float(modifier.get("player_prop_relevance_adjustment", 0.0) or 0.0)
    team_adjustment = float(modifier.get("team_market_confidence_adjustment", 0.0) or 0.0)
    for key in PLAYER_PROP_MARKETS:
        scores[key] += player_adjustment
    for key in TEAM_MARKETS:
        scores[key] += team_adjustment
    scores = {key: round(clamp(value), 2) for key, value in scores.items()}
    no_bet = []
    caps = {}
    if lineup_certainty < 55 and market in PLAYER_PROP_MARKETS | TACTICAL_MARKETS:
        caps["lineup_sensitive_markets"] = "confirmed_lineup_missing_cap"
        no_bet.append("confirmed_lineup_missing_caps_player_tactical_markets")
    if keeper_certainty < 55 and market in TEAM_MARKETS | {"saves", "goalkeeper_saves"}:
        caps["goalkeeper_sensitive_markets"] = "confirmed_goalkeeper_missing_cap"
        no_bet.append("confirmed_goalkeeper_missing_caps_team_total_markets")
    if red_vol >= 65 and market == "correct_score":
        caps["correct_score"] = "red_card_volatility_and_calibration_cap"
        no_bet.append("red_card_volatility_caps_correct_score")
    if market == "correct_score":
        caps["correct_score"] = caps.get("correct_score", "correct_score_extra_calibration_cap")
    if market in FIRST_HALF_MARKETS and first_half <= 0:
        caps["first_half_markets"] = "first_half_context_missing_cap"
        no_bet.append("first_half_context_missing_full_game_signal_not_enough")
    return finalize_soccer_response(
        {
            "market_relevance_scores": scores,
            "strongest_market_links": compact_list(_top_links(scores), limit=12),
            "weak_market_links": [key for key, value in scores.items() if value < 35.0][:12],
            "no_bet_market_reasons": compact_list(no_bet, limit=20),
            "player_prop_relevance": round(max((scores.get(key, 0.0) for key in PLAYER_PROP_MARKETS), default=0.0), 2),
            "team_market_relevance": round(max((scores.get(key, 0.0) for key in TEAM_MARKETS), default=0.0), 2),
            "tactical_market_relevance": round(max((scores.get(key, 0.0) for key in TACTICAL_MARKETS), default=0.0), 2),
            "referee_market_relevance": round(max((scores.get(key, 0.0) for key in REFEREE_MARKETS), default=0.0), 2),
            "set_piece_market_relevance": round(max((scores.get(key, 0.0) for key in SET_PIECE_MARKETS), default=0.0), 2),
            "market_confidence_caps": caps,
            "selected_market_type": market,
            "selected_market_relevance_score": scores.get(market, 0.0),
            "edge_fabricated": False,
        },
        source_payload=source,
    )
