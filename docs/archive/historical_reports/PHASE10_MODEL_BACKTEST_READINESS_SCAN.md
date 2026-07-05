# Phase 10 Model / Backtest Readiness Scan

Generated: 2026-06-12T19:09:43

- HEAD: `ef175eb`
- Git clean at scan start: `True`

## Baseline Validation
- main import: `PASS`
- scheduler_runner compile: `PASS`
- main compile: `PASS`

## Repo Size
- Python files scanned: `715`
- Total files scanned: `1089`

## Capability Map

### model_training
- Files with hits: `267`

| File | Line | Match |
|---|---:|---|
| `main.py` | 47 | `AutomationCalibrationCollectorRunRequest,` |
| `main.py` | 48 | `AutomationCalibrationCollectorScheduledRunRequest,` |
| `main.py` | 72 | `import multi_sport_model_registry` |
| `main.py` | 78 | `compact_calibration_response,` |
| `multi_sport_model_registry.py` | 335 | `GLOBAL_MODEL_REGISTRY_RULES = [` |
| `multi_sport_model_registry.py` | 352 | `"calibration_requirements",` |
| `multi_sport_model_registry.py` | 385 | `"probability bucket calibration",` |
| `multi_sport_model_registry.py` | 389 | `STANDARD_CALIBRATION_REQUIREMENTS = [` |
| `quant_engine.py` | 338 | `"backtest_requirements": ["settled outcomes", "closing-line history", "probability calibration buckets"],` |
| `quant_engine.py` | 339 | `"calibration_requirements": ["edge bucket calibration", "Kelly drawdown review", "confidence calibration"],` |
| `screenshot_intake.py` | 5 | `import multi_sport_model_registry` |
| `screenshot_intake.py` | 149 | `sport_key = multi_sport_model_registry.normalize_sport_key(str(ticket.get("sport") or ""))` |
| `screenshot_intake.py` | 150 | `normalization = multi_sport_model_registry.normalize_sport_inputs_for_model(` |
| `screenshot_intake.py` | 218 | `model_analysis = multi_sport_model_registry.analyze_sport_model(model_payload)` |
| `automation_scheduler/advanced_red_team_report.py` | 89 | `calibration_records: list[Mapping[str, Any]] \| None = None,` |
| `automation_scheduler/advanced_red_team_report.py` | 106 | `calibration_records=calibration_records,` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 54 | `("sliding_window_topology", "Sliding Window Time-Series Topology", "calibration_only", "deterministic_fallback_ready"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 55 | `("graph_density_clustering", "Graph Density Clustering", "calibration_only", "deterministic_fallback_ready"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 56 | `("information_theory", "Information-Theory Diagnostics", "active_calibration", "deterministic_fallback_ready"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 57 | `("conformal_uncertainty", "Conformal Prediction", "blocked_insufficient_data", "needs_calibration_outcomes"),` |
| `automation_scheduler/backtesting.py` | 5 | `from .calibration import calculate_calibration_metrics, summarize_outcome_coverage` |
| `automation_scheduler/backtesting.py` | 50 | `status = "metrics_ready" if coverage["settled_count"] >= len(rows) else "partial_calibration"` |
| `automation_scheduler/backtesting.py` | 60 | `"metrics": calculate_calibration_metrics(rows),` |
| `automation_scheduler/backtesting_engine.py` | 8 | `from .calibration_tracker import (` |
| `automation_scheduler/backtesting_engine.py` | 10 | `calculate_expected_calibration_error,` |
| `automation_scheduler/backtesting_engine.py` | 89 | `Path(base_data_dir, "calibration").mkdir(parents=True, exist_ok=True)` |
| `automation_scheduler/backtesting_engine.py` | 109 | `ece = calculate_expected_calibration_error(paper_rows)` |
| `automation_scheduler/baseball_data_availability.py` | 43 | `"calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),` |
| `automation_scheduler/baseball_data_availability.py` | 71 | `calibration_context: dict[str, Any] \| None = None,` |
| `automation_scheduler/baseball_data_availability.py` | 89 | `calibration_context,` |
| `automation_scheduler/baseball_data_availability.py` | 116 | `calibration_allowed = "calibration_outcomes" in available` |
| `automation_scheduler/baseball_impact_calibration.py` | 12 | `def evaluate_baseball_impact_calibration(` |
| `automation_scheduler/baseball_impact_calibration.py` | 29 | `status = "insufficient_data" if matched < 30 else "partial_calibration" if matched < 100 else "calibration_ready"` |
| `automation_scheduler/baseball_impact_calibration.py` | 43 | `"calibration_status": status,` |
| `automation_scheduler/baseball_impact_calibration.py` | 49 | `"confidence_cap": 35.0 if status == "insufficient_data" else 68.0 if status == "partial_calibration" else 88.0,` |
| `automation_scheduler/baseball_impact_common.py` | 83 | `"CALIBRATION_ONLY",` |
| `automation_scheduler/baseball_impact_readiness.py` | 33 | `"calibration_requirements": [` |
| `automation_scheduler/baseball_impact_readiness.py` | 43 | `"heavy_ml_training_added": False,` |
| `automation_scheduler/baseball_impact_readiness.py` | 53 | `"fabricated_calibration",` |
| `automation_scheduler/baseball_impact_red_team.py` | 21 | `calibration: dict[str, Any] \| None = None,` |
| `automation_scheduler/baseball_impact_red_team.py` | 35 | `cal = calibration or {}` |
| `automation_scheduler/baseball_impact_red_team.py` | 102 | `if cal.get("calibration_status") == "insufficient_data":` |
| `automation_scheduler/baseball_impact_red_team.py` | 103 | `reasons.append("calibration_missing")` |
| `automation_scheduler/baseball_impact_report.py` | 10 | `from .baseball_impact_calibration import evaluate_baseball_impact_calibration` |
| `automation_scheduler/baseball_impact_report.py` | 52 | `def _recommend(*, tier: int, market: str, selected_relevance: float, calibration_status: str, no_bet: list[str], pitcher_allowed: bool, batter_allowed: bool, red_team_adjustment: str) -> str:` |
| `automation_scheduler/baseball_impact_report.py` | 63 | `if calibration_status == "calibration_ready" and selected_relevance >= 70:` |
| `automation_scheduler/baseball_impact_report.py` | 65 | `if calibration_status == "insufficient_data":` |
| `automation_scheduler/basketball_player_impact.py` | 8 | `from .basketball_player_impact_calibration import evaluate_basketball_player_impact_calibration` |
| `automation_scheduler/basketball_player_impact.py` | 219 | `calibration = evaluate_basketball_player_impact_calibration(source, outcome_records or [], market_type=source.get("market_type") or source.get("market"))` |
| `automation_scheduler/basketball_player_impact.py` | 243 | `insufficient_sample=bool(calibration.get("insufficient_sample", True)),` |
| `automation_scheduler/basketball_player_impact.py` | 268 | `"calibration": calibration,` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 87 | `error = safe_float(record.get("calibration_error"))` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 115 | `"calibration_error": round(avg_error, 4),` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 120 | `"calibration_status": "insufficient_sample" if insufficient else ("calibrated_watch" if avg_error <= 0.12 else "calibration_warning"),` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 124 | `def evaluate_basketball_player_impact_calibration(` |
| `automation_scheduler/basketball_player_impact_common.py` | 43 | `"calibration_bucket_prefix": "basketball_nba.player_impact",` |
| `automation_scheduler/basketball_player_impact_common.py` | 50 | `"calibration_bucket_prefix": "basketball_wnba.player_impact",` |
| `automation_scheduler/basketball_player_impact_common.py` | 57 | `"calibration_bucket_prefix": "basketball_ncaab.player_impact",` |
| `automation_scheduler/basketball_player_impact_common.py` | 64 | `"calibration_bucket_prefix": "basketball_ncaaw.player_impact",` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 16 | `"market_specific_calibration",` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 33 | `"calibration_bucket_prefix": contract["calibration_bucket_prefix"],` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 53 | `"calibration_ready": True,` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 27 | `calibration = result.get("calibration") if isinstance(result.get("calibration"), dict) else {}` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 41 | `if calibration.get("insufficient_sample", True):` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 42 | `reasons.append("low_calibration_support")` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 43 | `missing.extend(calibration.get("next_required_data") or ["settled_outcomes"])` |
| `automation_scheduler/calibration.py` | 13 | `CALIBRATION_SCHEMA_VERSION = f"{SCHEMA_VERSION}.outcome_calibration.v1"` |
| `automation_scheduler/calibration.py` | 35 | `path = resolve_base_data_dir(base_data_dir) / "calibration"` |
| `automation_scheduler/calibration.py` | 217 | `row["calibration_bucket"] = outcome_match.get("calibration_bucket", row.get("calibration_bucket"))` |
| `automation_scheduler/calibration.py` | 375 | `def calculate_calibration_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:` |
| `automation_scheduler/calibration_collector.py` | 13 | `from .calibration import build_calibration_report` |
| `automation_scheduler/calibration_collector.py` | 24 | `COLLECTOR_SCHEMA_VERSION = f"{SCHEMA_VERSION}.kalshi_calibration_collector.v1"` |
| `automation_scheduler/calibration_collector.py` | 65 | `configured_hard_cap = max(1, _env_int("KALSHI_CALIBRATION_MAX_DAILY_NEW_CONTRACTS_HARD_CAP", DEFAULT_DAILY_NEW_CONTRACT_HARD_CAP))` |
| `automation_scheduler/calibration_collector.py` | 66 | `legacy_daily_target = _env_int("KALSHI_CALIBRATION_MAX_NEW_CONTRACTS_PER_DAY", DEFAULT_DAILY_NEW_CONTRACT_TARGET)` |
| `automation_scheduler/calibration_tracker.py` | 7 | `CALIBRATION_BUCKETS: tuple[tuple[float, float, str], ...] = (` |
| `automation_scheduler/calibration_tracker.py` | 34 | `for lower, upper, label in CALIBRATION_BUCKETS:` |
| `automation_scheduler/calibration_tracker.py` | 41 | `buckets: dict[str, list[dict[str, float]]] = {label: [] for _, _, label in CALIBRATION_BUCKETS}` |
| `automation_scheduler/calibration_tracker.py` | 81 | `def summarize_calibration_by_bucket(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:` |
| `automation_scheduler/candlestick_manifold_detector.py` | 12 | `calibration_report: dict[str, Any] \| None = None,` |
| `automation_scheduler/candlestick_manifold_detector.py` | 21 | `calibration_report=calibration_report,` |
| `automation_scheduler/collector_scheduled_runner.py` | 7 | `from .calibration_collector import run_collector_cycle` |
| `automation_scheduler/combat_availability_context.py` | 20 | `camp = weighted_average(((score_from_range(source.get("camp_length"), low=0.0, high=12.0), 0.4), (score_from_range(source.get("training_camp_length"), low=0.0, high=12.0), 0.3), (100.0 - (score_from_range(source.get("cam` |
| `automation_scheduler/combat_data_availability.py` | 33 | `"camp_context": ("camp_length", "camp_change_context", "team_change_context", "training_camp_length"),` |
| `automation_scheduler/combat_data_availability.py` | 37 | `"calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),` |
| `automation_scheduler/combat_data_availability.py` | 67 | `calibration_context: dict[str, Any] \| None = None,` |
| `automation_scheduler/combat_data_availability.py` | 86 | `calibration_context,` |
| `automation_scheduler/combat_impact_calibration.py` | 18 | `def evaluate_combat_impact_calibration(` |
| `automation_scheduler/combat_impact_calibration.py` | 37 | `status = "insufficient_data" if sample == 0 else "partial_calibration" if insufficient else "calibration_ready"` |
| `automation_scheduler/combat_impact_calibration.py` | 46 | `"calibration_status": status,` |
| `automation_scheduler/combat_impact_calibration.py` | 62 | `"calibration_buckets": {` |
| `automation_scheduler/combat_impact_common.py` | 111 | `"CALIBRATION_ONLY",` |
| `automation_scheduler/combat_impact_readiness.py` | 45 | `"calibration_requirements": [` |
| `automation_scheduler/combat_impact_readiness.py` | 71 | `"fabricated_calibration",` |
| `automation_scheduler/combat_impact_red_team.py` | 22 | `calibration: dict[str, Any] \| None = None,` |
| `automation_scheduler/combat_impact_red_team.py` | 36 | `calib = calibration or {}` |
| `automation_scheduler/combat_impact_red_team.py` | 85 | `if market in {"exact_round", "winning_method_round"} and calib.get("calibration_status") != "calibration_ready":` |
| `automation_scheduler/combat_impact_red_team.py` | 87 | `if market == "split_decision" and calib.get("calibration_status") != "calibration_ready":` |
| `automation_scheduler/combat_impact_report.py` | 9 | `from .combat_impact_calibration import evaluate_combat_impact_calibration` |
| `automation_scheduler/combat_impact_report.py` | 38 | `def _recommend(*, tier: int, market: str, calibration_status: str, selected: float, no_bet: list[str], red_team_adjustment: str, fighter_allowed: bool) -> str:` |
| `automation_scheduler/combat_impact_report.py` | 43 | `if calibration_status == "insufficient_data":` |
| `automation_scheduler/combat_impact_report.py` | 46 | `return "CALIBRATION_ONLY"` |
| `automation_scheduler/combat_market_relevance.py` | 123 | `caps["exact_round"] = "extra_conservative_calibration_required"` |
| `automation_scheduler/combat_market_relevance.py` | 124 | `no_bet.append("exact_round_market_heavily_calibration_capped")` |
| `automation_scheduler/combat_pace_cardio_context.py` | 15 | `cardio = weighted_average(((score_from_range(source.get("cardio_rating_proxy"), low=0.0, high=1.0), 0.35), (score_from_range(source.get("five_round_performance"), low=0.0, high=1.0), 0.25), (100.0 - (decline or 0.0), 0.2` |
| `automation_scheduler/conformal_uncertainty.py` | 32 | `calibration_records: list[Mapping[str, Any]] \| None = None,` |
| `automation_scheduler/conformal_uncertainty.py` | 37 | `residuals = sorted(res for res in (_residual(row) for row in (calibration_records or [])) if res is not None)` |
| `automation_scheduler/conformal_uncertainty.py` | 49 | `"conformal_no_bet_reason": "insufficient_calibration_outcomes",` |
| `automation_scheduler/conformal_uncertainty.py` | 51 | `"blocked_reason": "calibration_outcome_count_below_minimum",` |
| `automation_scheduler/cross_asset_embedding_router.py` | 44 | `"calibration_status": manifold_state.get("calibration_status"),` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 87 | `"active_calibration_count": maturity.get("active_calibration_count"),` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 88 | `"calibration_only_count": maturity.get("calibration_only_count"),` |
| `automation_scheduler/cross_asset_manifold_router.py` | 6 | `from .manifold_calibration import build_manifold_calibration_report, load_manifold_calibration_report` |
| `automation_scheduler/cross_asset_manifold_router.py` | 38 | `calibration_report: dict[str, Any] \| None = None,` |
| `automation_scheduler/cross_asset_manifold_router.py` | 47 | `calibration_report=calibration_report,` |
| `automation_scheduler/cross_asset_manifold_router.py` | 55 | `calibration_report=calibration_report,` |
| `automation_scheduler/data_availability_tiers.py` | 37 | `0: "outcome_backfill_and_tier_0_calibration_only",` |
| `automation_scheduler/data_availability_tiers.py` | 38 | `1: "baseline_training_and_tier_1_calibration",` |
| `automation_scheduler/data_availability_tiers.py` | 39 | `2: "market_aware_review_and_tier_2_calibration",` |
| `automation_scheduler/data_availability_tiers.py` | 40 | `3: "advanced_stats_review_with_tier_3_calibration",` |
| `automation_scheduler/data_intelligence_registry.py` | 33 | `"calibration_outcome_tracking",` |
| `automation_scheduler/data_intelligence_registry.py` | 39 | `"xgboost",` |
| `automation_scheduler/data_intelligence_registry.py` | 40 | `"lightgbm",` |
| `automation_scheduler/data_intelligence_registry.py` | 92 | `"active_calibration_models": maturity.get("active_calibration_count", 0),` |
| `automation_scheduler/data_paths.py` | 97 | `def get_calibration_reports_dir() -> Path:` |
| `automation_scheduler/data_paths.py` | 98 | `return get_runtime_data_path("calibration")` |

### backtesting
- Files with hits: `313`

| File | Line | Match |
|---|---:|---|
| `asian_markets.py` | 79 | `half_loss_probability: float` |
| `asian_markets.py` | 81 | `full_loss_probability: float` |
| `asian_markets.py` | 91 | `If goal_diff_distribution provided (net goals vs line side), approximate win/push/half outcomes.` |
| `asian_markets.py` | 102 | `half_loss_probability=0.25 if is_quarter else 0.0,` |
| `bet_log.py` | 44 | `"profit_loss",` |
| `bet_log.py` | 115 | `def calculate_profit_loss(result: str \| None, stake: Any, odds_american: Any) -> float:` |
| `bet_log.py` | 121 | `if normalized in {"loss", "lost"}:` |
| `bet_log.py` | 214 | `entry["status"] = "closed" if str(result).lower() in {"win", "won", "loss", "lost", "push"} else entry.get("status")` |
| `main.py` | 31 | `from src.api.model_backtest_routes import register_model_backtest_routes` |
| `main.py` | 35 | `from src.api.automation_review_outcomes_routes import register_automation_review_outcomes_routes` |
| `main.py` | 58 | `AutomationOutcomeIngestRequest,` |
| `main.py` | 59 | `AutomationOutcomeLocalSettlementImportRequest,` |
| `multi_sport_model_registry.py` | 338 | `"Confirmed bets require backtest proof, risk approval, and clear no-bet flags.",` |
| `multi_sport_model_registry.py` | 339 | `"No sport may be promoted without backtesting and logging.",` |
| `multi_sport_model_registry.py` | 351 | `"backtest_requirements",` |
| `multi_sport_model_registry.py` | 378 | `"historical odds and closing-line dataset",` |
| `quant_engine.py` | 157 | `"profit_or_loss": 0,` |
| `quant_engine.py` | 278 | `"""Total overround / vig for N outcomes: sum(implied) - 1."""` |
| `quant_engine.py` | 338 | `"backtest_requirements": ["settled outcomes", "closing-line history", "probability calibration buckets"],` |
| `quant_engine.py` | 339 | `"calibration_requirements": ["edge bucket calibration", "Kelly drawdown review", "confidence calibration"],` |
| `risk_engine.py` | 61 | `def max_loss_correlated_bets(stakes: list[float], correlation_matrix_max: float = 1.0) -> float:` |
| `risk_engine.py` | 68 | `def drawdown_tracker(equity_series: list[float]) -> dict[str, Any]:` |
| `risk_engine.py` | 70 | `return {"max_drawdown_pct": None, "current_drawdown_pct": None}` |
| `risk_engine.py` | 80 | `return {"max_drawdown_pct": round(max_dd * 100, 2), "current_drawdown_pct": round(cur_dd * 100, 2)}` |
| `screenshot_intake.py` | 75 | `"social signal not backtested",` |
| `automation_scheduler/advanced_red_team_report.py` | 87 | `historical_records: list[Mapping[str, Any]] \| None = None,` |
| `automation_scheduler/advanced_red_team_report.py` | 104 | `historical_records=historical_records,` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 57 | `("conformal_uncertainty", "Conformal Prediction", "blocked_insufficient_data", "needs_calibration_outcomes"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 58 | `("contrastive_embedding", "Contrastive Embedding Diagnostics", "research_only", "needs_labeled_outcomes"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 85 | `if _num(value) is not None and key.lower() not in {"final_outcome", "outcome", "label", "target"}` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 94 | `if _num(value) is not None and key.lower() not in {"final_outcome", "outcome", "label", "target"}:` |
| `automation_scheduler/backtesting.py` | 5 | `from .calibration import calculate_calibration_metrics, summarize_outcome_coverage` |
| `automation_scheduler/backtesting.py` | 28 | `def run_backtesting_scaffold(rows: list[dict[str, Any]] \| None = None) -> dict[str, Any]:` |
| `automation_scheduler/backtesting.py` | 30 | `coverage = summarize_outcome_coverage(rows)` |
| `automation_scheduler/backtesting.py` | 31 | `if not rows or coverage["settled_count"] == 0:` |
| `automation_scheduler/backtesting_engine.py` | 11 | `calculate_log_loss,` |
| `automation_scheduler/backtesting_engine.py` | 15 | `from .historical_replay import load_historical_rows, replay_rows, summarize_replay_result, write_replay_result` |
| `automation_scheduler/backtesting_engine.py` | 29 | `def _paper_rows_from_replay_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:` |
| `automation_scheduler/backtesting_engine.py` | 36 | `pnl = stake * (odds / 100.0) if odds >= 100 else stake * (100.0 / abs(odds)) if odds <= -100 else 0.0` |
| `automation_scheduler/bankroll_state.py` | 38 | `"current_drawdown_percent": 0.0,` |
| `automation_scheduler/bankroll_state.py` | 43 | `"closed_pnl": 0.0,` |
| `automation_scheduler/baseball_data_availability.py` | 43 | `"calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),` |
| `automation_scheduler/baseball_data_availability.py` | 116 | `calibration_allowed = "calibration_outcomes" in available` |
| `automation_scheduler/baseball_data_availability.py` | 128 | `cap_reasons.append("calibration_outcomes_missing")` |
| `automation_scheduler/baseball_data_availability.py` | 139 | `next_data.append("settled_outcomes_by_market_role_context")` |
| `automation_scheduler/baseball_impact_calibration.py` | 21 | `predictions = _records(source.get("historical_predictions"))` |
| `automation_scheduler/baseball_impact_calibration.py` | 22 | `outcomes = _records(source.get("settled_outcomes"))` |
| `automation_scheduler/baseball_impact_calibration.py` | 23 | `explicit = int(safe_float(source.get("matched_outcomes_count"), 0.0) or 0)` |
| `automation_scheduler/baseball_impact_calibration.py` | 25 | `if predictions and outcomes:` |
| `automation_scheduler/baseball_impact_readiness.py` | 35 | `"real_settled_outcomes_required",` |
| `automation_scheduler/baseball_impact_readiness.py` | 37 | `"realized_returns_required_for_roi_proxy",` |
| `automation_scheduler/baseball_impact_red_team.py` | 104 | `missing.extend(cal.get("next_required_data") or ["settled_outcomes"])` |
| `automation_scheduler/basketball_player_impact.py` | 194 | `outcome_records: list[dict[str, Any]] \| None = None,` |
| `automation_scheduler/basketball_player_impact.py` | 219 | `calibration = evaluate_basketball_player_impact_calibration(source, outcome_records or [], market_type=source.get("market_type") or source.get("market"))` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 71 | `profits: list[float] = []` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 73 | `outcome = str(record.get("outcome") or record.get("result") or "").strip().lower()` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 76 | `hit = outcome in {"hit", "win", "won", "success", "covered", "over_hit", "under_hit"}` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 79 | `elif outcome or record.get("hit") is not None:` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 60 | `"minutes_outcomes",` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 61 | `"settled_market_outcomes",` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 43 | `missing.extend(calibration.get("next_required_data") or ["settled_outcomes"])` |
| `automation_scheduler/bayesian_structural_baseline.py` | 30 | `value = _num(row.get("outcome_value") or row.get("actual") or row.get("return") or row.get("delta"))` |
| `automation_scheduler/bayesian_structural_baseline.py` | 54 | `observed = _num(candidate.get("observed_outcome") or candidate.get("observed_value") or candidate.get("edge_estimate")) or mean` |
| `automation_scheduler/calibration.py` | 8 | `from .outcome_store import load_outcome_records, load_outcome_state, summarize_outcomes` |
| `automation_scheduler/calibration.py` | 13 | `CALIBRATION_SCHEMA_VERSION = f"{SCHEMA_VERSION}.outcome_calibration.v1"` |
| `automation_scheduler/calibration.py` | 14 | `_OUTCOME_KEYS = ("outcome_status", "settlement_status", "final_outcome", "paper_result", "settled_at")` |
| `automation_scheduler/calibration.py` | 55 | `def _normalized_outcome_label(value: Any) -> float \| None:` |
| `automation_scheduler/calibration_collector.py` | 17 | `from .outcome_store import ingest_outcome_records, load_outcome_records` |
| `automation_scheduler/calibration_collector.py` | 29 | `SETTLED_CLASSIFICATIONS = {"settled_yes", "settled_no", "void_or_cancelled"}` |
| `automation_scheduler/calibration_collector.py` | 83 | `"min_target_outcomes": _env_int("KALSHI_CALIBRATION_MIN_TARGET_OUTCOMES", 30),` |
| `automation_scheduler/calibration_collector.py` | 84 | `"good_target_outcomes": _env_int("KALSHI_CALIBRATION_GOOD_TARGET_OUTCOMES", 100),` |
| `automation_scheduler/calibration_tracker.py` | 24 | `def _to_outcome(value: Any) -> float \| None:` |
| `automation_scheduler/calibration_tracker.py` | 28 | `if status == "loss":` |
| `automation_scheduler/calibration_tracker.py` | 44 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/calibration_tracker.py` | 58 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/candlestick_manifold_detector.py` | 13 | `historical_records: list[dict[str, Any]] \| None = None,` |
| `automation_scheduler/candlestick_manifold_detector.py` | 22 | `historical_records=historical_records,` |
| `automation_scheduler/candlestick_manifold_detector.py` | 36 | `"historical_pattern_cluster_performance": {` |
| `automation_scheduler/candlestick_manifold_detector.py` | 37 | `"historical_win_rate": result.get("historical_win_rate"),` |
| `automation_scheduler/candlestick_pattern_detector.py` | 190 | `"stop_loss_level": round(stop, 6),` |
| `automation_scheduler/causal_scaffold.py` | 14 | `"outcome_variable": "player_usage_or_prop_line_move",` |
| `automation_scheduler/causal_scaffold.py` | 20 | `"outcome_variable": "total_or_points_prop_hit_rate",` |
| `automation_scheduler/causal_scaffold.py` | 26 | `"outcome_variable": "fake_edge_or_negative_ev_rate",` |
| `automation_scheduler/causal_scaffold.py` | 32 | `"outcome_variable": "momentum_follow_through",` |
| `automation_scheduler/collector_scheduled_runner.py` | 15 | `"persist_outcomes": True,` |
| `automation_scheduler/collector_scheduled_runner.py` | 44 | `"infer_outcomes",` |
| `automation_scheduler/collector_scheduled_runner.py` | 45 | `"inferred_outcomes",` |
| `automation_scheduler/collector_scheduled_runner.py` | 46 | `"allow_inferred_outcomes",` |
| `automation_scheduler/combat_damage_durability_context.py` | 31 | `if source.get("ko_losses") not in (None, "") and any_metric("knockdowns_absorbed") in (None, ""):` |
| `automation_scheduler/combat_data_availability.py` | 15 | `"basic_record_context": ("wins", "losses", "draws", "fighter_a_wins", "fighter_b_wins", "recent_wins", "recent_losses"),` |
| `automation_scheduler/combat_data_availability.py` | 16 | `"finish_history_context": ("finish_rate", "decision_rate", "ko_wins", "submission_wins", "ko_losses", "submission_losses"),` |
| `automation_scheduler/combat_data_availability.py` | 37 | `"calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),` |
| `automation_scheduler/combat_data_availability.py` | 132 | `calibration_allowed = "calibration_outcomes" in available` |
| `automation_scheduler/combat_impact_calibration.py` | 11 | `def _count_outcomes(payload: dict[str, Any]) -> int:` |
| `automation_scheduler/combat_impact_calibration.py` | 12 | `outcomes = payload.get("settled_outcomes")` |
| `automation_scheduler/combat_impact_calibration.py` | 13 | `if isinstance(outcomes, list):` |
| `automation_scheduler/combat_impact_calibration.py` | 14 | `return len(outcomes)` |
| `automation_scheduler/combat_impact_common.py` | 325 | `"simulation_only": True,` |
| `automation_scheduler/combat_impact_readiness.py` | 39 | `"moneyline": ["fighter_identity", "summary_striking_grappling", "settled_moneyline_outcomes"],` |
| `automation_scheduler/combat_impact_readiness.py` | 40 | `"method_markets": ["finish_path_outcomes", "durability_context", "submission_control_context"],` |
| `automation_scheduler/combat_impact_readiness.py` | 41 | `"round_total_markets": ["round_level_pace_damage", "cardio_decline_context", "finish_timing_outcomes"],` |
| `automation_scheduler/combat_impact_readiness.py` | 43 | `"boxing_props": ["jab_power_punch_tracking", "round_projection", "settled_boxing_prop_outcomes"],` |
| `automation_scheduler/combat_impact_red_team.py` | 96 | `missing.extend(calib.get("next_required_data") or ["settled_combat_market_outcomes"])` |
| `automation_scheduler/combat_incentive_context.py` | 15 | `urgency = score_from_range(source.get("post_loss_urgency_context"), low=0.0, high=1.0) or 0.0` |
| `automation_scheduler/conformal_uncertainty.py` | 21 | `actual = _num(row.get("actual") or row.get("realized_edge") or row.get("outcome"))` |
| `automation_scheduler/conformal_uncertainty.py` | 34 | `minimum_outcomes: int = 50,` |
| `automation_scheduler/conformal_uncertainty.py` | 38 | `if len(residuals) < int(minimum_outcomes):` |
| `automation_scheduler/conformal_uncertainty.py` | 49 | `"conformal_no_bet_reason": "insufficient_calibration_outcomes",` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 8 | `def _outcome_label(row: Mapping[str, Any]) -> str \| None:` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 9 | `value = str(row.get("final_outcome") or row.get("outcome") or row.get("label") or row.get("paper_result") or "").strip().lower()` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 10 | `if value in {"win", "yes", "true", "1", "profitable", "profit"}:` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 11 | `return "profitable"` |
| `automation_scheduler/cross_asset_embedding_router.py` | 6 | `from .market_state_manifold import nearest_historical_neighbors` |
| `automation_scheduler/cross_asset_embedding_router.py` | 15 | `historical_records: list[dict[str, Any]] \| None = None,` |
| `automation_scheduler/cross_asset_embedding_router.py` | 21 | `neighbors = nearest_historical_neighbors(manifold_features, historical_records or [])` |
| `automation_scheduler/cross_asset_embedding_router.py` | 24 | `historical_records=historical_records,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 29 | `historical_records: list[dict[str, Any]] \| None = None,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 30 | `total_labeled_outcomes: int = 0,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 31 | `outcome_coverage_by_asset_type: dict[str, Any] \| None = None,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 38 | `historical_records=historical_records,` |
| `automation_scheduler/cross_asset_manifold_router.py` | 39 | `historical_records: list[dict[str, Any]] \| None = None,` |
| `automation_scheduler/cross_asset_manifold_router.py` | 48 | `historical_records=historical_records,` |
| `automation_scheduler/cross_asset_manifold_router.py` | 56 | `historical_records=historical_records,` |
| `automation_scheduler/cross_asset_manifold_router.py` | 64 | `historical_records=historical_records,` |

### feature_engineering
- Files with hits: `594`

| File | Line | Match |
|---|---:|---|
| `api_server.py` | 8 | `"/api/betting/events/active",` |
| `api_server.py` | 9 | `"/api/actions/betting/events/active",` |
| `api_server.py` | 10 | `"/api/actions/betting/events/{event_id}/odds",` |
| `api_server.py` | 11 | `"/api/actions/betting/first-event-odds",` |
| `asian_markets.py` | 7 | `from quant_engine import american_to_decimal, implied_probability_from_american` |
| `asian_markets.py` | 126 | `p_us = implied_probability_from_american(american_spread_price)` |
| `asian_markets.py` | 225 | `def mlb_weather_adjustment() -> dict[str, Any]:` |
| `asian_markets.py` | 226 | `return mlb_adjustment_placeholder("weather")` |
| `bet_decision_engine.py` | 1 | `"""Bet decision rules and line evaluation orchestration for Action endpoints."""` |
| `bet_decision_engine.py` | 11 | `edge_percentage,` |
| `bet_decision_engine.py` | 13 | `implied_probability_from_american,` |
| `bet_decision_engine.py` | 20 | `EDGE_STRONG_BET = 2.5` |
| `bet_log.py` | 10 | `from src.core.math_utils import american_to_decimal, american_to_implied_probability` |
| `bet_log.py` | 18 | `"event_id",` |
| `bet_log.py` | 19 | `"event",` |
| `bet_log.py` | 28 | `"model_level",` |
| `config.py` | 45 | `self.log_level = os.getenv("LOG_LEVEL", "INFO")` |
| `full_board_engine.py` | 16 | `"manual_review_required": [],` |
| `full_board_engine.py` | 24 | `str(value.get("event") or value.get("event_id") or "").strip().lower(),` |
| `full_board_engine.py` | 52 | `def build_full_board_preview(ticket: dict[str, Any], model_analysis: dict[str, Any], provider_enrichment: dict[str, Any]) -> dict[str, Any]:` |
| `full_board_engine.py` | 54 | `model_board = model_analysis.get("full_board_preview") if isinstance(model_analysis, dict) else None` |
| `logbook_engine.py` | 11 | `"event": ticket.get("event"),` |
| `logbook_engine.py` | 17 | `"model_level": model_analysis.get("model_level"),` |
| `logbook_engine.py` | 20 | `"implied_probability": model_analysis.get("implied_probability"),` |
| `logbook_engine.py` | 21 | `"edge_percent": model_analysis.get("edge"),` |
| `logger_setup.py` | 5 | `def setup_logger(log_file: str, log_level: str = "INFO") -> logging.Logger:` |
| `logger_setup.py` | 11 | `log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)` |
| `logger_setup.py` | 16 | `# Convert string log level to logging constant` |
| `logger_setup.py` | 17 | `numeric_level = getattr(logging, log_level.upper(), logging.INFO)` |
| `main.py` | 34 | `from src.api.automation_sport_impact_routes import register_automation_sport_impact_routes` |
| `main.py` | 35 | `from src.api.automation_review_outcomes_routes import register_automation_review_outcomes_routes` |
| `main.py` | 37 | `from src.api.automation_manifold_routes import register_automation_manifold_routes` |
| `main.py` | 45 | `AutomationBaseballImpactDiagnosticsRequest,` |
| `market_pricing.py` | 8 | `closing_line_value_pct as _core_closing_line_value_pct,` |
| `market_pricing.py` | 11 | `steam_move_from_implied_series,` |
| `market_pricing.py` | 15 | `american_to_implied_probability as implied_probability_from_american,` |
| `market_pricing.py` | 25 | `implied_probability_from_american(american_a),` |
| `model_blender.py` | 1 | `"""Blend model probability with market-derived probabilities (never invent model inputs)."""` |
| `model_blender.py` | 29 | `def confidence_score(edge_percent: float, num_books: int = 1) -> int:` |
| `model_blender.py` | 30 | `base = 40 + edge_percent * 2.5 + min(20, num_books * 3)` |
| `model_probability.py` | 15 | `weather_adjustment: Optional[float] = None,` |
| `model_probability.py` | 18 | `injury_adjustment: Optional[float] = None,` |
| `model_probability.py` | 23 | `closing_line_projection: Optional[float] = None,` |
| `model_probability.py` | 27 | `self.weather_adjustment = weather_adjustment` |
| `multi_sport_model_registry.py` | 11 | `edge_percentage,` |
| `multi_sport_model_registry.py` | 16 | `implied_probability_from_american,` |
| `multi_sport_model_registry.py` | 31 | `MODEL_LEVEL_NOT_BUILT = "not_built"` |
| `multi_sport_model_registry.py` | 32 | `MODEL_LEVEL_MARKET_DERIVED_ONLY = "market_derived_only"` |
| `parlay_engine.py` | 14 | `def parlay_implied_probability(american_odds: list[int \| float]) -> float:` |
| `parlay_engine.py` | 36 | `def parlay_ev(` |
| `parlay_engine.py` | 40 | `"""EV per $1 staked on parlay."""` |
| `parlay_engine.py` | 58 | `def same_game_parlay_risk_warning(legs_same_event: bool) -> bool:` |
| `quant_engine.py` | 6 | `american_to_implied_probability as _core_american_to_implied_probability,` |
| `quant_engine.py` | 9 | `break_even_probability_american as _core_break_even_probability_american,` |
| `quant_engine.py` | 10 | `break_even_probability_decimal as _core_break_even_probability_decimal,` |
| `quant_engine.py` | 12 | `decimal_to_implied_probability as _core_decimal_to_implied_probability,` |
| `risk_engine.py` | 91 | `Very rough Monte-Carlo-free upper bound using gambler's ruin approximation for even bets.` |
| `risk_engine.py` | 238 | `candidate_type = candidate.get("candidate_type") or "positive_ev"` |
| `risk_engine.py` | 239 | `base_roi = float(candidate.get("estimated_roi_percent") or candidate.get("ev_percent") or 0.0)` |
| `risk_engine.py` | 265 | `"review_only": True,` |
| `screenshot_intake.py` | 6 | `from full_board_engine import build_full_board_preview` |
| `screenshot_intake.py` | 19 | `str(value.get("event") or value.get("event_id") or "").strip().lower(),` |
| `screenshot_intake.py` | 43 | `collect_from_container(response.get("full_board_preview"))` |
| `screenshot_intake.py` | 49 | `collect_from_container(model_analysis.get("full_board_preview"))` |
| `sharp_client.py` | 91 | `def get_sharp_active_events(` |
| `sharp_client.py` | 99 | `url = f"{SHARP_BASE_URL}/events"` |
| `sharp_client.py` | 119 | `"message": "SharpAPI active events request failed",` |
| `sharp_client.py` | 131 | `message = "SharpAPI active events lookup completed"` |
| `automation_scheduler/advanced_red_team_provider_policy.py` | 62 | `def evaluate_advanced_red_team_provider(provider: str \| None = None) -> dict[str, Any]:` |
| `automation_scheduler/advanced_red_team_report.py` | 113 | `fake_edge_count = sum(1 for row in diagnostics if "static_correlation_not_predictive" in list(row.get("no_bet_reasons") or []))` |
| `automation_scheduler/advanced_red_team_report.py` | 127 | `"fake_edge_warning_count": fake_edge_count,` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 6 | `from .advanced_red_team_provider_policy import evaluate_advanced_red_team_provider` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 70 | `"affects_review_queue": True,` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 80 | `def _vector_from_record(record: Mapping[str, Any], *, feature_names: list[str] \| None = None) -> list[float]:` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 82 | `keys = feature_names or sorted(` |
| `automation_scheduler/ai_provider_security.py` | 6 | `from .audit_ledger import append_security_event` |
| `automation_scheduler/ai_provider_security.py` | 8 | `from .security_event_types import AI_PROVIDER_REJECTED, AI_PROVIDER_SELECTED, FORBIDDEN_PROVIDER_REJECTED` |
| `automation_scheduler/ai_provider_security.py` | 54 | `def evaluate_ai_provider(` |
| `automation_scheduler/ai_provider_security.py` | 86 | `append_security_event(` |
| `automation_scheduler/alert_engine.py` | 40 | `review_queue_gate_result = str(candidate.get("review_queue_gate_result") or "")` |
| `automation_scheduler/alert_engine.py` | 41 | `if governance_status == "blocked_by_governance" or review_queue_gate_result == "blocked_by_governance":` |
| `automation_scheduler/alert_engine.py` | 50 | `"governance_status": "blocked_by_governance" if "blocked_by_governance" in base_blockers else "review_required",` |
| `automation_scheduler/alert_engine.py` | 60 | `review_items: list[dict[str, Any]],` |
| `automation_scheduler/arbitrage_detector.py` | 22 | `(str(offer.get("event_name") or ""), str(offer.get("market") or ""))` |
| `automation_scheduler/arbitrage_detector.py` | 26 | `return {"candidate_found": False, "reason": "mismatched_event_market", "candidate_type": None}` |
| `automation_scheduler/audit_ledger.py` | 10 | `from .security_event_types import normalize_event_type` |
| `automation_scheduler/audit_ledger.py` | 45 | `def append_security_event(` |
| `automation_scheduler/audit_ledger.py` | 47 | `event_type: str,` |
| `automation_scheduler/audit_ledger.py` | 63 | `event_type = normalize_event_type(event_type)` |
| `automation_scheduler/backtesting_engine.py` | 17 | `from .paper_trade_ledger import load_paper_ledger, summarize_paper_ledger` |
| `automation_scheduler/backtesting_engine.py` | 58 | `"ev_percent": row.get("ev_percent", 0.0),` |
| `automation_scheduler/backtesting_engine.py` | 71 | `status = "needs_revalidation"` |
| `automation_scheduler/backtesting_engine.py` | 146 | `calibration_status = "needs_revalidation"` |
| `automation_scheduler/balance_sheet_risk.py` | 44 | `def evaluate_balance_sheet(row: dict[str, Any] \| None) -> dict[str, Any]:` |
| `automation_scheduler/balance_sheet_risk.py` | 110 | `warnings.append("elevated_debt_to_equity")` |
| `automation_scheduler/balance_sheet_risk.py` | 142 | `force_status = "NO_REVIEW"` |
| `automation_scheduler/balance_sheet_risk.py` | 144 | `force_status = "HIGH_RISK_REVIEW"` |
| `automation_scheduler/baseball_availability_context.py` | 5 | `from .baseball_impact_common import boolish, clamp, compact_list, finalize_baseball_response, missing_fields, score_from_range, weighted_average` |
| `automation_scheduler/baseball_availability_context.py` | 9 | `"player_injury_status",` |
| `automation_scheduler/baseball_availability_context.py` | 10 | `"pitcher_injury_status",` |
| `automation_scheduler/baseball_availability_context.py` | 25 | `"weather_delay_risk",` |
| `automation_scheduler/baseball_batter_impact.py` | 5 | `from .baseball_impact_common import clamp, compact_list, finalize_baseball_response, missing_fields, score_centered, score_from_range, weighted_average` |
| `automation_scheduler/baseball_batter_impact.py` | 36 | `"injury_status",` |
| `automation_scheduler/baseball_batter_impact.py` | 45 | `def evaluate_baseball_batter_impact(row: dict[str, Any] \| None = None, *, batter_level_allowed: bool = True, data_tier: int \| None = None) -> dict[str, Any]:` |
| `automation_scheduler/baseball_batter_impact.py` | 47 | `if not batter_level_allowed and not any(source.get(k) not in (None, "", []) for k in ("lineup_slot", "plate_appearances_projection", "confirmed_lineup")):` |
| `automation_scheduler/baseball_bullpen_context.py` | 5 | `from .baseball_impact_common import boolish, clamp, compact_list, finalize_baseball_response, missing_fields, score_from_range, weighted_average` |
| `automation_scheduler/baseball_bullpen_context.py` | 18 | `"back_to_back_relievers",` |
| `automation_scheduler/baseball_bullpen_context.py` | 19 | `"unavailable_relievers",` |
| `automation_scheduler/baseball_bullpen_context.py` | 23 | `"high_leverage_usage",` |
| `automation_scheduler/baseball_data_availability.py` | 5 | `from .baseball_impact_common import (` |
| `automation_scheduler/baseball_data_availability.py` | 28 | `"pitch_level_context": ("pitch_run_value", "whiff_rate", "chase_rate", "zone_rate", "called_strike_plus_whiff_proxy"),` |
| `automation_scheduler/baseball_data_availability.py` | 37 | `"bullpen_context": ("bullpen_era_proxy", "bullpen_fip_proxy", "bullpen_recent_pitch_count", "closer_available", "unavailable_relievers"),` |
| `automation_scheduler/baseball_data_availability.py` | 39 | `"weather_context": ("wind_speed", "wind_direction", "temperature", "humidity", "precipitation_risk", "air_density_proxy"),` |
| `automation_scheduler/baseball_defense_baserunning_context.py` | 5 | `from .baseball_impact_common import clamp, compact_list, finalize_baseball_response, missing_fields, score_from_range, weighted_average` |
| `automation_scheduler/baseball_defense_baserunning_context.py` | 27 | `def evaluate_baseball_defense_baserunning_context(row: dict[str, Any] \| None = None) -> dict[str, Any]:` |
| `automation_scheduler/baseball_defense_baserunning_context.py` | 49 | `"defense_impact_score": round(clamp(defense or 0.0), 2),` |
| `automation_scheduler/baseball_defense_baserunning_context.py` | 50 | `"baserunning_impact_score": round(clamp(baserun or 0.0), 2),` |
| `automation_scheduler/baseball_impact_calibration.py` | 5 | `from .baseball_impact_common import compact_list, finalize_baseball_response, normalize_baseball_market, normalize_baseball_role, normalize_baseball_sport, safe_float` |
| `automation_scheduler/baseball_impact_calibration.py` | 12 | `def evaluate_baseball_impact_calibration(` |
| `automation_scheduler/baseball_impact_calibration.py` | 38 | `predicted = str(pred.get("prediction") or pred.get("recommended_action") or "").lower() in {"over", "yes", "win", "review", "positive", "1", "true"}` |
| `automation_scheduler/baseball_impact_calibration.py` | 62 | `"weather_bucket": source.get("weather_bucket") or source.get("park_weather_bucket"),` |
| `automation_scheduler/baseball_impact_common.py` | 81 | `ALLOWED_BASEBALL_REVIEW_STATUSES = (` |
| `automation_scheduler/baseball_impact_common.py` | 84 | `"WATCHLIST_REVIEW",` |
| `automation_scheduler/baseball_impact_common.py` | 85 | `"ACTIVE_REVIEW",` |
| `automation_scheduler/baseball_impact_common.py` | 87 | `"MARKET_REVIEW_ONLY",` |
| `automation_scheduler/baseball_impact_readiness.py` | 6 | `from .baseball_impact_common import DATA_TIER_REQUIREMENTS, SUPPORTED_BASEBALL_MARKETS, SUPPORTED_BASEBALL_ROLES, SUPPORTED_BASEBALL_SPORTS, finalize_baseball_response` |
| `automation_scheduler/baseball_impact_readiness.py` | 9 | `def build_baseball_impact_readiness() -> dict[str, Any]:` |
| `automation_scheduler/baseball_impact_readiness.py` | 12 | `"status": "baseball_impact_readiness",` |
| `automation_scheduler/baseball_impact_readiness.py` | 27 | `"pitcher_outs_recorded": ["confirmed_starter", "pitch_count_limit", "recent_pitch_count", "weather_delay_risk"],` |
| `automation_scheduler/baseball_impact_red_team.py` | 5 | `from .baseball_impact_common import PLAYER_PROP_MARKETS, clamp, compact_list, finalize_baseball_response, normalize_baseball_market` |
| `automation_scheduler/baseball_impact_red_team.py` | 8 | `def evaluate_baseball_impact_red_team(` |
| `automation_scheduler/baseball_impact_red_team.py` | 12 | `run_value_impact: dict[str, Any] \| None = None,` |
| `automation_scheduler/baseball_impact_red_team.py` | 13 | `pitcher_impact: dict[str, Any] \| None = None,` |
| `automation_scheduler/baseball_impact_report.py` | 5 | `from .baseball_availability_context import evaluate_baseball_availability_context` |
| `automation_scheduler/baseball_impact_report.py` | 6 | `from .baseball_batter_impact import evaluate_baseball_batter_impact` |
| `automation_scheduler/baseball_impact_report.py` | 7 | `from .baseball_bullpen_context import evaluate_baseball_bullpen_context` |
| `automation_scheduler/baseball_impact_report.py` | 8 | `from .baseball_data_availability import evaluate_baseball_data_availability` |
| `automation_scheduler/baseball_incentive_context.py` | 5 | `from .baseball_impact_common import boolish, clamp, compact_list, finalize_baseball_response, missing_fields, present_fields, score_from_range, weighted_average` |
| `automation_scheduler/baseball_incentive_context.py` | 21 | `"revenge_narrative_context",` |
| `automation_scheduler/baseball_incentive_context.py` | 40 | `def evaluate_baseball_incentive_context(row: dict[str, Any] \| None = None) -> dict[str, Any]:` |
| `automation_scheduler/baseball_incentive_context.py` | 53 | `"market_relevance_modifier": {"modifier_only": True},` |
| `automation_scheduler/baseball_lineup_context.py` | 5 | `from .baseball_impact_common import boolish, clamp, compact_list, finalize_baseball_response, missing_fields, safe_float, score_from_range, weighted_average` |
| `automation_scheduler/baseball_lineup_context.py` | 30 | `def evaluate_baseball_lineup_context(row: dict[str, Any] \| None = None) -> dict[str, Any]:` |
| `automation_scheduler/baseball_market_relevance.py` | 5 | `from .baseball_impact_common import BATTER_PROP_MARKETS, PITCHER_PROP_MARKETS, TEAM_MARKETS, clamp, compact_list, finalize_baseball_response, normalize_baseball_market, weighted_average` |
| `automation_scheduler/baseball_market_relevance.py` | 12 | `def evaluate_baseball_market_relevance(` |
| `automation_scheduler/baseball_market_relevance.py` | 16 | `run_value_impact: dict[str, Any] \| None = None,` |
| `automation_scheduler/baseball_market_relevance.py` | 17 | `pitcher_impact: dict[str, Any] \| None = None,` |

### bankroll
- Files with hits: `170`

| File | Line | Match |
|---|---:|---|
| `api_server.py` | 20 | `"/api/actions/betting/bankroll-summary",` |
| `asian_markets.py` | 62 | `"""Split a quarter (.25) handicap/total into two half-stake legs on adjacent half lines."""` |
| `bet_decision_engine.py` | 10 | `confidence_adjusted_stake,` |
| `bet_decision_engine.py` | 14 | `kelly_fraction,` |
| `bet_decision_engine.py` | 17 | `suggested_stake,` |
| `bet_decision_engine.py` | 70 | `def risk_grade_from_kelly(full_kelly_pct: float) -> str:` |
| `bet_log.py` | 25 | `"stake",` |
| `bet_log.py` | 26 | `"unit_size",` |
| `bet_log.py` | 27 | `"bankroll_at_bet",` |
| `bet_log.py` | 36 | `"kelly_percent",` |
| `logbook_engine.py` | 23 | `"stake": 0,` |
| `logbook_engine.py` | 24 | `"risk_profile": ticket.get("risk_profile"),` |
| `main.py` | 153 | `exposure_check,` |
| `main.py` | 155 | `kelly_fraction,` |
| `main.py` | 158 | `suggested_stake,` |
| `main.py` | 414 | `exposure_check_fn=exposure_check,` |
| `multi_sport_model_registry.py` | 14 | `fractional_kelly_percent,` |
| `multi_sport_model_registry.py` | 15 | `full_kelly_percent,` |
| `multi_sport_model_registry.py` | 17 | `risk_profile_settings,` |
| `multi_sport_model_registry.py` | 18 | `suggested_stake_with_risk_controls,` |
| `parlay_engine.py` | 4 | `from quant_engine import american_to_decimal, kelly_fraction` |
| `parlay_engine.py` | 40 | `"""EV per $1 staked on parlay."""` |
| `parlay_engine.py` | 46 | `def parlay_kelly(` |
| `parlay_engine.py` | 50 | `"""Kelly fraction treating parlay as single binary bet."""` |
| `quant_engine.py` | 20 | `fractional_kelly as _core_fractional_kelly,` |
| `quant_engine.py` | 21 | `fractional_kelly_percent as _core_fractional_kelly_percent,` |
| `quant_engine.py` | 22 | `full_kelly_fraction as _core_full_kelly_fraction,` |
| `quant_engine.py` | 23 | `full_kelly_percent as _core_full_kelly_percent,` |
| `risk_engine.py` | 1 | `"""Bankroll and exposure risk calculations (stateless helpers)."""` |
| `risk_engine.py` | 7 | `from src.core.math_utils import calculate_kelly_stake` |
| `risk_engine.py` | 10 | `RISK_PROFILE_SETTINGS = {` |
| `risk_engine.py` | 11 | `"conservative": {"risk_profile": "conservative", "kelly_fraction": 0.125, "max_bankroll_pct": 0.01, "confidence_multiplier": 0.75},` |
| `screenshot_intake.py` | 183 | `"bankroll": ticket.get("bankroll"),` |
| `screenshot_intake.py` | 184 | `"unit_size": ticket.get("unit_size"),` |
| `screenshot_intake.py` | 185 | `"risk_profile": ticket.get("risk_profile") or "conservative",` |
| `screenshot_intake.py` | 213 | `"bankroll": ticket.get("bankroll"),` |
| `automation_scheduler/arbitrage_detector.py` | 13 | `total_stake: float = 100.0,` |
| `automation_scheduler/arbitrage_detector.py` | 36 | `total_stake=total_stake,` |
| `automation_scheduler/backtesting_engine.py` | 33 | `stake = _to_float(row.get("paper_stake"), default=1.0)` |
| `automation_scheduler/backtesting_engine.py` | 36 | `pnl = stake * (odds / 100.0) if odds >= 100 else stake * (100.0 / abs(odds)) if odds <= -100 else 0.0` |
| `automation_scheduler/backtesting_engine.py` | 39 | `pnl = -stake` |
| `automation_scheduler/backtesting_engine.py` | 56 | `"paper_stake": stake,` |
| `automation_scheduler/bankroll_state.py` | 10 | `SCHEMA_VERSION = "bankroll_state_v1"` |
| `automation_scheduler/bankroll_state.py` | 14 | `return get_runtime_data_path("bankroll")` |
| `automation_scheduler/bankroll_state.py` | 32 | `def default_bankroll_state(starting_bankroll: float = 10000.0) -> dict[str, Any]:` |
| `automation_scheduler/bankroll_state.py` | 34 | `"bankroll_id": f"bankroll_{uuid4().hex[:12]}",` |
| `automation_scheduler/combat_incentive_context.py` | 11 | `ranking = score_from_range(source.get("ranking_stakes_context"), low=0.0, high=1.0) or 0.0` |
| `automation_scheduler/combat_incentive_context.py` | 18 | `narrative = "low" if any(source.get(key) not in (None, "") for key in ("title_fight_context", "title_eliminator_context", "ranking_stakes_context", "performance_bonus_motivation")) else "high"` |
| `automation_scheduler/data_availability_tiers.py` | 135 | `"stock": _profile(module="stock", display_name="Stocks", tier0=["symbol", "date", "close_price", "return"], tier1=["rolling_return", "volatility", "drawdown", "volume", "trend"], tier2=["market_benchmark", "sector_benchm` |
| `automation_scheduler/data_availability_tiers.py` | 136 | `"crypto": _profile(module="crypto", display_name="Crypto", tier0=["symbol", "timestamp", "price", "return"], tier1=["rolling_return", "volatility", "volume", "drawdown", "trend"], tier2=["order_book", "spread", "liquidit` |
| `automation_scheduler/data_availability_tiers.py` | 194 | `"historical_prices": {"historical_prices", "date", "close_price", "return", "rolling_return", "volatility", "drawdown", "trend"},` |
| `automation_scheduler/data_availability_tiers.py` | 210 | `"ohlcv": {"ohlcv", "price", "volume", "return", "rolling_return", "volatility", "drawdown"},` |
| `automation_scheduler/data_intelligence_registry.py` | 66 | `"no_raw_payload_exposure": True,` |
| `automation_scheduler/data_intelligence_registry.py` | 67 | `"no_auth_signature_api_key_secret_exposure": True,` |
| `automation_scheduler/data_source_registry.py` | 121 | `"drawdown_risk_score",` |
| `automation_scheduler/data_source_registry.py` | 153 | `"drawdown_risk_score",` |
| `automation_scheduler/data_source_registry.py` | 166 | `"stake",` |
| `automation_scheduler/data_source_registry.py` | 288 | `"paper_only_portfolio_simulation",` |
| `automation_scheduler/deepseek_prompt_contracts.py` | 62 | `"repeated_model_mistakes": [],` |
| `automation_scheduler/deepseek_response_validator.py` | 68 | `"repeated_model_mistakes",` |
| `automation_scheduler/deepseek_response_validator.py` | 326 | `"repeated_model_mistakes": [],` |
| `automation_scheduler/deepseek_response_validator.py` | 395 | `"repeated_model_mistakes": _coerce_list(raw.get("repeated_model_mistakes"), limit=25),` |
| `automation_scheduler/derived_feature_planner.py` | 24 | `"drawdown": {"fields": ["close_price"], "history": 5},` |
| `automation_scheduler/drawdown_controls.py` | 6 | `def apply_drawdown_controls(stake_fraction: float, state: dict[str, Any]) -> dict[str, Any]:` |
| `automation_scheduler/drawdown_controls.py` | 7 | `drawdown = float(state.get("current_drawdown_percent", 0))` |
| `automation_scheduler/drawdown_controls.py` | 9 | `adjusted = max(0.0, float(stake_fraction))` |
| `automation_scheduler/drawdown_controls.py` | 11 | `if drawdown >= 20:` |
| `automation_scheduler/ev_line_shopper.py` | 16 | `stake: float,` |
| `automation_scheduler/ev_line_shopper.py` | 24 | `ev_value = calculate_ev(stake, probability, offer["odds"])` |
| `automation_scheduler/ev_line_shopper.py` | 29 | `"ev_percent": round((ev_value / stake) * 100.0, 6),` |
| `automation_scheduler/ev_line_shopper.py` | 30 | `"estimated_roi_percent": round(calculate_roi(stake, ev_value), 6),` |
| `automation_scheduler/exposure_limits.py` | 6 | `EXPOSURE_LIMITS as LIMITS,` |
| `automation_scheduler/exposure_limits.py` | 7 | `apply_all_exposure_caps as _risk_apply_all_exposure_caps,` |
| `automation_scheduler/exposure_limits.py` | 8 | `cap_correlated_exposure as _risk_cap_correlated_exposure,` |
| `automation_scheduler/exposure_limits.py` | 9 | `cap_daily_exposure as _risk_cap_daily_exposure,` |
| `automation_scheduler/golf_course_fit_context.py` | 27 | `"wind_exposure",` |
| `automation_scheduler/golf_course_fit_context.py` | 74 | `wind_exposure = _cat(source.get("wind_exposure"), {"low": 25.0, "below_average": 35.0, "moderate": 55.0, "medium": 55.0, "high": 78.0, "exposed": 88.0})` |
| `automation_scheduler/golf_course_fit_context.py` | 75 | `architecture = weighted_average(((length, 0.25), (width, 0.25), (100.0 - rough if rough is not None else None, 0.2), (green_size, 0.2), (green_speed, 0.15), (100.0 - (hazard or 50.0), 0.25), (par5, 0.2), (wind_exposure, ` |
| `automation_scheduler/golf_data_availability.py` | 31 | `"course_architecture_context": ("course_length", "par", "fairway_width", "rough_difficulty", "green_size", "green_speed", "wind_exposure"),` |
| `automation_scheduler/kelly_staking.py` | 7 | `kelly_binary_fraction_from_decimal,` |
| `automation_scheduler/kelly_staking.py` | 8 | `scale_kelly_fraction,` |
| `automation_scheduler/kelly_staking.py` | 12 | `KELLY_PARAMS = {` |
| `automation_scheduler/kelly_staking.py` | 13 | `"kelly_mode": "full_kelly_primary",` |
| `automation_scheduler/liquidity_risk.py` | 16 | `def estimate_limit_risk(limit_estimate: Any, target_stake: Any) -> float:` |
| `automation_scheduler/liquidity_risk.py` | 18 | `stake_value = max(0.0, float(target_stake or 0))` |
| `automation_scheduler/liquidity_risk.py` | 19 | `if stake_value == 0:` |
| `automation_scheduler/liquidity_risk.py` | 21 | `return round(clamp(1 - (limit_value / stake_value), 0, 1), 4)` |
| `automation_scheduler/market_state_graph.py` | 34 | `{"path": ["credit_spread", "risk_off_regime", "etf_drawdown_risk"], "hypothesis": "credit_spread_widening_increases_risk_off_etf_pressure", "fields": ["credit_spread_score", "risk_on_risk_off_score"]},` |
| `automation_scheduler/market_state_manifold.py` | 355 | `"recommended_unit_size": 0,` |
| `automation_scheduler/middle_opportunity_detector.py` | 14 | `stake_per_side: float = 100.0,` |
| `automation_scheduler/middle_opportunity_detector.py` | 42 | `stake_per_side=stake_per_side,` |
| `automation_scheduler/model_performance_report.py` | 41 | `"max_drawdown_percent": float(report.get("max_drawdown_percent", 0.0)),` |
| `automation_scheduler/model_recheck_runner.py` | 19 | `"bankroll": candidate.get("bankroll", 1000),` |
| `automation_scheduler/model_recheck_runner.py` | 20 | `"unit_size": candidate.get("unit_size", 25),` |
| `automation_scheduler/model_recheck_runner.py` | 21 | `"risk_profile": candidate.get("risk_profile", "medium"),` |
| `automation_scheduler/odds_math.py` | 69 | `def calculate_payout(stake: Any, odds: Any, *, odds_format: str = "american") -> float:` |
| `automation_scheduler/odds_math.py` | 70 | `return round(_core_calculate_payout(stake, odds, odds_format=odds_format), 6)` |
| `automation_scheduler/odds_math.py` | 73 | `def calculate_profit_loss(stake: Any, odds: Any, *, won: bool, odds_format: str = "american") -> float:` |
| `automation_scheduler/odds_math.py` | 74 | `return round(_core_calculate_profit_loss(stake, odds, won=won, odds_format=odds_format), 6)` |
| `automation_scheduler/paper_trade_ledger.py` | 38 | `def _profit_for_win(stake: float, american_odds: float) -> float:` |
| `automation_scheduler/paper_trade_ledger.py` | 40 | `return stake * (american_odds / 100.0)` |
| `automation_scheduler/paper_trade_ledger.py` | 42 | `return stake * (100.0 / abs(american_odds))` |
| `automation_scheduler/paper_trade_ledger.py` | 86 | `"recommended_kelly_mode": payload.get("recommended_kelly_mode", "fractional"),` |
| `automation_scheduler/pattern_calibration.py` | 126 | `kelly = None` |
| `automation_scheduler/pattern_calibration.py` | 129 | `kelly = win_rate - ((1.0 - win_rate) / payoff)` |
| `automation_scheduler/pattern_calibration.py` | 159 | `"kelly_percentage": round(kelly * 100.0, 6) if kelly is not None else None,` |
| `automation_scheduler/pattern_calibration.py` | 160 | `"fractional_kelly_paper_only": round(max(0.0, kelly or 0.0) * 0.25 * 100.0, 6) if kelly is not None else None,` |
| `automation_scheduler/performance_metrics.py` | 15 | `def _max_drawdown_percent(entries: list[dict[str, Any]], starting_equity: float = 100.0) -> float:` |
| `automation_scheduler/performance_metrics.py` | 18 | `max_drawdown = 0.0` |
| `automation_scheduler/performance_metrics.py` | 26 | `drawdown = (peak - equity) / peak * 100.0` |
| `automation_scheduler/performance_metrics.py` | 27 | `if drawdown > max_drawdown:` |
| `automation_scheduler/response_compactor.py` | 3075 | `"repeated_model_mistakes": list(report.get("repeated_model_mistakes") or [])[:25],` |
| `automation_scheduler/response_compactor.py` | 3451 | `"max_drawdown_percent": float(payload.get("max_drawdown_percent", 0.0)),` |
| `automation_scheduler/review_queue.py` | 251 | `"raw_full_kelly_fraction": candidate.get("raw_full_kelly_fraction"),` |
| `automation_scheduler/review_queue.py` | 252 | `"operating_full_kelly_fraction": candidate.get("operating_full_kelly_fraction"),` |
| `automation_scheduler/review_queue.py` | 254 | `"recommended_kelly_mode": candidate.get("recommended_kelly_mode"),` |
| `automation_scheduler/review_queue.py` | 255 | `"stake_confidence_score": candidate.get("stake_confidence_score"),` |
| `automation_scheduler/risk_limit_guard.py` | 15 | `"max_correlation_exposure": None,` |
| `automation_scheduler/risk_limit_guard.py` | 16 | `"max_provider_exposure": None,` |
| `automation_scheduler/risk_limit_guard.py` | 17 | `"max_asset_class_exposure": None,` |

### ledger_clv_outcomes
- Files with hits: `278`

| File | Line | Match |
|---|---:|---|
| `api_server.py` | 21 | `"/api/actions/betting/clv-report",` |
| `asian_markets.py` | 75 | `class AsianHandicapSettlement:` |
| `asian_markets.py` | 88 | `) -> AsianHandicapSettlement:` |
| `asian_markets.py` | 91 | `If goal_diff_distribution provided (net goals vs line side), approximate win/push/half outcomes.` |
| `asian_markets.py` | 98 | `return AsianHandicapSettlement(` |
| `bet_log.py` | 9 | `from src.core.clv import price_ratio_clv_percent` |
| `bet_log.py` | 42 | `"clv_percent",` |
| `bet_log.py` | 130 | `def calculate_clv_percent(actual_odds_taken: Any, closing_odds: Any) -> float \| None:` |
| `bet_log.py` | 131 | `return price_ratio_clv_percent(actual_odds_taken, closing_odds)` |
| `main.py` | 35 | `from src.api.automation_review_outcomes_routes import register_automation_review_outcomes_routes` |
| `main.py` | 58 | `AutomationOutcomeIngestRequest,` |
| `main.py` | 59 | `AutomationOutcomeLocalSettlementImportRequest,` |
| `main.py` | 60 | `AutomationSettlementDiscoveryRequest,` |
| `market_pricing.py` | 7 | `from src.core.clv import (` |
| `market_pricing.py` | 8 | `closing_line_value_pct as _core_closing_line_value_pct,` |
| `market_pricing.py` | 10 | `opening_vs_current_clv_implied_change_pct as _core_opening_vs_current_clv_implied_change_pct,` |
| `market_pricing.py` | 113 | `def opening_vs_current_clv_implied_change_pct(` |
| `model_probability.py` | 307 | `"clv_provider_status": "placeholder"` |
| `model_probability.py` | 313 | `"injury_provider_status", "player_projection_provider_status", "clv_provider_status"` |
| `multi_sport_model_registry.py` | 379 | `"backtesting dataset with settled outcomes",` |
| `multi_sport_model_registry.py` | 383 | `"settled outcomes by sport, market, and prop type",` |
| `multi_sport_model_registry.py` | 6293 | `"clv": None,` |
| `quant_engine.py` | 278 | `"""Total overround / vig for N outcomes: sum(implied) - 1."""` |
| `quant_engine.py` | 338 | `"backtest_requirements": ["settled outcomes", "closing-line history", "probability calibration buckets"],` |
| `risk_engine.py` | 6 | `from src.core.clv import average_clv as _core_average_clv` |
| `risk_engine.py` | 302 | `def average_clv(clv_values: list[Optional[float]]) -> Optional[float]:` |
| `risk_engine.py` | 303 | `return _core_average_clv(clv_values)` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 57 | `("conformal_uncertainty", "Conformal Prediction", "blocked_insufficient_data", "needs_calibration_outcomes"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 58 | `("contrastive_embedding", "Contrastive Embedding Diagnostics", "research_only", "needs_labeled_outcomes"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 70 | `"affects_review_queue": True,` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 85 | `if _num(value) is not None and key.lower() not in {"final_outcome", "outcome", "label", "target"}` |
| `automation_scheduler/alert_engine.py` | 40 | `review_queue_gate_result = str(candidate.get("review_queue_gate_result") or "")` |
| `automation_scheduler/alert_engine.py` | 41 | `if governance_status == "blocked_by_governance" or review_queue_gate_result == "blocked_by_governance":` |
| `automation_scheduler/backtesting.py` | 5 | `from .calibration import calculate_calibration_metrics, summarize_outcome_coverage` |
| `automation_scheduler/backtesting.py` | 30 | `coverage = summarize_outcome_coverage(rows)` |
| `automation_scheduler/backtesting.py` | 31 | `if not rows or coverage["settled_count"] == 0:` |
| `automation_scheduler/backtesting.py` | 36 | `"settled_count": 0,` |
| `automation_scheduler/backtesting_engine.py` | 14 | `from .clv_tracker import calculate_clv_for_american_odds` |
| `automation_scheduler/backtesting_engine.py` | 17 | `from .paper_trade_ledger import load_paper_ledger, summarize_paper_ledger` |
| `automation_scheduler/backtesting_engine.py` | 37 | `settlement_status = "settled"` |
| `automation_scheduler/backtesting_engine.py` | 40 | `settlement_status = "settled"` |
| `automation_scheduler/baseball_data_availability.py` | 43 | `"calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),` |
| `automation_scheduler/baseball_data_availability.py` | 116 | `calibration_allowed = "calibration_outcomes" in available` |
| `automation_scheduler/baseball_data_availability.py` | 128 | `cap_reasons.append("calibration_outcomes_missing")` |
| `automation_scheduler/baseball_data_availability.py` | 139 | `next_data.append("settled_outcomes_by_market_role_context")` |
| `automation_scheduler/baseball_impact_calibration.py` | 22 | `outcomes = _records(source.get("settled_outcomes"))` |
| `automation_scheduler/baseball_impact_calibration.py` | 23 | `explicit = int(safe_float(source.get("matched_outcomes_count"), 0.0) or 0)` |
| `automation_scheduler/baseball_impact_calibration.py` | 25 | `if predictions and outcomes:` |
| `automation_scheduler/baseball_impact_calibration.py` | 26 | `outcome_ids = {str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")) for item in outcomes}` |
| `automation_scheduler/baseball_impact_readiness.py` | 35 | `"real_settled_outcomes_required",` |
| `automation_scheduler/baseball_impact_readiness.py` | 36 | `"open_close_prices_required_for_clv_proxy",` |
| `automation_scheduler/baseball_impact_red_team.py` | 104 | `missing.extend(cal.get("next_required_data") or ["settled_outcomes"])` |
| `automation_scheduler/basketball_player_impact.py` | 194 | `outcome_records: list[dict[str, Any]] \| None = None,` |
| `automation_scheduler/basketball_player_impact.py` | 219 | `calibration = evaluate_basketball_player_impact_calibration(source, outcome_records or [], market_type=source.get("market_type") or source.get("market"))` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 67 | `clv: list[float] = []` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 73 | `outcome = str(record.get("outcome") or record.get("result") or "").strip().lower()` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 76 | `hit = outcome in {"hit", "win", "won", "success", "covered", "over_hit", "under_hit"}` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 79 | `elif outcome or record.get("hit") is not None:` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 60 | `"minutes_outcomes",` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 61 | `"settled_market_outcomes",` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 62 | `"closing_line_value",` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 43 | `missing.extend(calibration.get("next_required_data") or ["settled_outcomes"])` |
| `automation_scheduler/bayesian_structural_baseline.py` | 30 | `value = _num(row.get("outcome_value") or row.get("actual") or row.get("return") or row.get("delta"))` |
| `automation_scheduler/bayesian_structural_baseline.py` | 54 | `observed = _num(candidate.get("observed_outcome") or candidate.get("observed_value") or candidate.get("edge_estimate")) or mean` |
| `automation_scheduler/calibration.py` | 8 | `from .outcome_store import load_outcome_records, load_outcome_state, summarize_outcomes` |
| `automation_scheduler/calibration.py` | 9 | `from .paper_decision_ledger import load_paper_decisions, summarize_paper_decisions, to_float_or_none` |
| `automation_scheduler/calibration.py` | 10 | `from .review_queue import load_review_queue_state` |
| `automation_scheduler/calibration.py` | 13 | `CALIBRATION_SCHEMA_VERSION = f"{SCHEMA_VERSION}.outcome_calibration.v1"` |
| `automation_scheduler/calibration_collector.py` | 17 | `from .outcome_store import ingest_outcome_records, load_outcome_records` |
| `automation_scheduler/calibration_collector.py` | 18 | `from .paper_decision_ledger import LEDGER_SCHEMA_VERSION, create_paper_decision_record, load_paper_decisions` |
| `automation_scheduler/calibration_collector.py` | 19 | `from .review_queue import build_review_item, load_review_queue_state, persist_review_queue_snapshot, summarize_review_items` |
| `automation_scheduler/calibration_collector.py` | 22 | `from .settlement_discovery import classify_kalshi_settlement, discover_kalshi_settlements_for_pending_rows` |
| `automation_scheduler/calibration_tracker.py` | 24 | `def _to_outcome(value: Any) -> float \| None:` |
| `automation_scheduler/calibration_tracker.py` | 44 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/calibration_tracker.py` | 58 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/calibration_tracker.py` | 72 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/causal_discovery_research.py` | 10 | `"prediction_market": ["liquidity", "time_to_close", "settlement_uncertainty", "news_catalyst"],` |
| `automation_scheduler/causal_scaffold.py` | 14 | `"outcome_variable": "player_usage_or_prop_line_move",` |
| `automation_scheduler/causal_scaffold.py` | 20 | `"outcome_variable": "total_or_points_prop_hit_rate",` |
| `automation_scheduler/causal_scaffold.py` | 26 | `"outcome_variable": "fake_edge_or_negative_ev_rate",` |
| `automation_scheduler/causal_scaffold.py` | 27 | `"confounders": ["liquidity", "time_to_close", "settlement_uncertainty", "news_catalyst"],` |
| `automation_scheduler/clv_tracker.py` | 8 | `from src.core.clv import (` |
| `automation_scheduler/clv_tracker.py` | 9 | `calculate_clv,` |
| `automation_scheduler/clv_tracker.py` | 10 | `calculate_clv_for_american_odds,` |
| `automation_scheduler/clv_tracker.py` | 11 | `calculate_clv_percent,` |
| `automation_scheduler/collector_scheduled_runner.py` | 15 | `"persist_outcomes": True,` |
| `automation_scheduler/collector_scheduled_runner.py` | 44 | `"infer_outcomes",` |
| `automation_scheduler/collector_scheduled_runner.py` | 45 | `"inferred_outcomes",` |
| `automation_scheduler/collector_scheduled_runner.py` | 46 | `"allow_inferred_outcomes",` |
| `automation_scheduler/combat_data_availability.py` | 37 | `"calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),` |
| `automation_scheduler/combat_data_availability.py` | 132 | `calibration_allowed = "calibration_outcomes" in available` |
| `automation_scheduler/combat_data_availability.py` | 149 | `next_data.append("settled_combat_market_outcomes")` |
| `automation_scheduler/combat_impact_calibration.py` | 11 | `def _count_outcomes(payload: dict[str, Any]) -> int:` |
| `automation_scheduler/combat_impact_calibration.py` | 12 | `outcomes = payload.get("settled_outcomes")` |
| `automation_scheduler/combat_impact_calibration.py` | 13 | `if isinstance(outcomes, list):` |
| `automation_scheduler/combat_impact_calibration.py` | 14 | `return len(outcomes)` |
| `automation_scheduler/combat_impact_readiness.py` | 39 | `"moneyline": ["fighter_identity", "summary_striking_grappling", "settled_moneyline_outcomes"],` |
| `automation_scheduler/combat_impact_readiness.py` | 40 | `"method_markets": ["finish_path_outcomes", "durability_context", "submission_control_context"],` |
| `automation_scheduler/combat_impact_readiness.py` | 41 | `"round_total_markets": ["round_level_pace_damage", "cardio_decline_context", "finish_timing_outcomes"],` |
| `automation_scheduler/combat_impact_readiness.py` | 43 | `"boxing_props": ["jab_power_punch_tracking", "round_projection", "settled_boxing_prop_outcomes"],` |
| `automation_scheduler/combat_impact_red_team.py` | 96 | `missing.extend(calib.get("next_required_data") or ["settled_combat_market_outcomes"])` |
| `automation_scheduler/conformal_uncertainty.py` | 21 | `actual = _num(row.get("actual") or row.get("realized_edge") or row.get("outcome"))` |
| `automation_scheduler/conformal_uncertainty.py` | 34 | `minimum_outcomes: int = 50,` |
| `automation_scheduler/conformal_uncertainty.py` | 38 | `if len(residuals) < int(minimum_outcomes):` |
| `automation_scheduler/conformal_uncertainty.py` | 49 | `"conformal_no_bet_reason": "insufficient_calibration_outcomes",` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 8 | `def _outcome_label(row: Mapping[str, Any]) -> str \| None:` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 9 | `value = str(row.get("final_outcome") or row.get("outcome") or row.get("label") or row.get("paper_result") or "").strip().lower()` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 72 | `rows = [row for row in (labeled_records or []) if isinstance(row, Mapping) and _outcome_label(row)]` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 85 | `"blocked_reason": "labeled_settled_record_count_below_minimum",` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 30 | `total_labeled_outcomes: int = 0,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 31 | `outcome_coverage_by_asset_type: dict[str, Any] \| None = None,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 44 | `total_labeled_outcomes=total_labeled_outcomes,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 45 | `outcome_coverage_by_asset_type=outcome_coverage_by_asset_type,` |
| `automation_scheduler/cross_asset_manifold_router.py` | 9 | `from .manifold_review_queue import build_manifold_review_queue, compact_manifold_review_response` |
| `automation_scheduler/cross_asset_manifold_router.py` | 86 | `queue = build_manifold_review_queue(` |
| `automation_scheduler/data_availability_tiers.py` | 18 | `0: "TIER_0_OUTCOME_BACKFILL",` |
| `automation_scheduler/data_availability_tiers.py` | 37 | `0: "outcome_backfill_and_tier_0_calibration_only",` |
| `automation_scheduler/data_availability_tiers.py` | 45 | `-1: "no-call audit for schedule/results/outcome fields",` |
| `automation_scheduler/data_availability_tiers.py` | 68 | `"prediction_market_outcome",` |
| `automation_scheduler/data_intelligence_registry.py` | 33 | `"calibration_outcome_tracking",` |
| `automation_scheduler/data_intelligence_registry.py` | 74 | `total_labeled_outcomes: int = 0,` |
| `automation_scheduler/data_intelligence_registry.py` | 75 | `outcome_coverage_by_asset_type: Mapping[str, Any] \| None = None,` |
| `automation_scheduler/data_intelligence_registry.py` | 78 | `total_labeled_outcomes=total_labeled_outcomes,` |
| `automation_scheduler/data_paths.py` | 73 | `def get_review_queue_dir() -> Path:` |
| `automation_scheduler/data_paths.py` | 74 | `return get_runtime_data_path("review_queue")` |
| `automation_scheduler/data_paths.py` | 77 | `def get_paper_ledger_dir() -> Path:` |
| `automation_scheduler/data_paths.py` | 78 | `return get_runtime_data_path("paper_ledger")` |

### leakage_risk
- Files with hits: `363`

| File | Line | Match |
|---|---:|---|
| `api_server.py` | 17 | `"/api/actions/betting/log-result",` |
| `asian_markets.py` | 91 | `If goal_diff_distribution provided (net goals vs line side), approximate win/push/half outcomes.` |
| `asian_markets.py` | 143 | `def mlb_market_grading_placeholder(market_type: str, result: str) -> dict[str, Any]:` |
| `asian_markets.py` | 147 | `"result": result,` |
| `asian_markets.py` | 157 | `def mlb_grade_full_game_moneyline(result: str) -> dict[str, Any]:` |
| `bet_decision_engine.py` | 131 | `return {"ok": False, "error": "INVALID_INPUT", "detail": "lines must be a non-empty list.", "results": []}` |
| `bet_decision_engine.py` | 134 | `return {"ok": False, "error": "INVALID_BANKROLL", "detail": "bankroll must be positive.", "results": []}` |
| `bet_decision_engine.py` | 137 | `return {"ok": False, "error": "INVALID_UNIT", "detail": "unit_size must be positive.", "results": []}` |
| `bet_decision_engine.py` | 157 | `return {"ok": False, "error": "INVALID_LINES", "detail": "No valid line objects.", "results": []}` |
| `bet_log.py` | 43 | `"result",` |
| `bet_log.py` | 115 | `def calculate_profit_loss(result: str \| None, stake: Any, odds_american: Any) -> float:` |
| `bet_log.py` | 116 | `normalized = (result or "").strip().lower()` |
| `bet_log.py` | 160 | `entry["result"] = entry.get("result") or "pending"` |
| `kalshi_client.py` | 23 | `result = {` |
| `kalshi_client.py` | 34 | `result.update({` |
| `kalshi_client.py` | 41 | `result.update({` |
| `kalshi_client.py` | 48 | `return result` |
| `main.py` | 35 | `from src.api.automation_review_outcomes_routes import register_automation_review_outcomes_routes` |
| `main.py` | 58 | `AutomationOutcomeIngestRequest,` |
| `main.py` | 59 | `AutomationOutcomeLocalSettlementImportRequest,` |
| `main.py` | 90 | `compact_outcome_ingest_response,` |
| `model_probability.py` | 75 | `class ModelProbabilityResult:` |
| `model_probability.py` | 76 | `"""Result of model probability calculation with transparency."""` |
| `model_probability.py` | 205 | `) -> ModelProbabilityResult:` |
| `model_probability.py` | 319 | `return ModelProbabilityResult(` |
| `multi_sport_model_registry.py` | 379 | `"backtesting dataset with settled outcomes",` |
| `multi_sport_model_registry.py` | 383 | `"settled outcomes by sport, market, and prop type",` |
| `multi_sport_model_registry.py` | 6220 | `["venue", "pitch condition", "toss result", "batting order", "bowling matchup", "run rate", "wicket rate", "weather"],` |
| `multi_sport_model_registry.py` | 10706 | `result = (team_goals - opponent_goals) + line` |
| `quant_engine.py` | 156 | `"result": "pending",` |
| `quant_engine.py` | 278 | `"""Total overround / vig for N outcomes: sum(implied) - 1."""` |
| `quant_engine.py` | 338 | `"backtest_requirements": ["settled outcomes", "closing-line history", "probability calibration buckets"],` |
| `risk_engine.py` | 222 | `"exposure_gate_result": "blocked" if blocked else "pass",` |
| `sharp_client.py` | 28 | `"result_type": "error",` |
| `sharp_client.py` | 77 | `"result_type": "odds" if has_actual_odds else "no_data",` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 57 | `("conformal_uncertainty", "Conformal Prediction", "blocked_insufficient_data", "needs_calibration_outcomes"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 58 | `("contrastive_embedding", "Contrastive Embedding Diagnostics", "research_only", "needs_labeled_outcomes"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 85 | `if _num(value) is not None and key.lower() not in {"final_outcome", "outcome", "label", "target"}` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 94 | `if _num(value) is not None and key.lower() not in {"final_outcome", "outcome", "label", "target"}:` |
| `automation_scheduler/alert_engine.py` | 40 | `review_queue_gate_result = str(candidate.get("review_queue_gate_result") or "")` |
| `automation_scheduler/alert_engine.py` | 41 | `if governance_status == "blocked_by_governance" or review_queue_gate_result == "blocked_by_governance":` |
| `automation_scheduler/backtesting.py` | 5 | `from .calibration import calculate_calibration_metrics, summarize_outcome_coverage` |
| `automation_scheduler/backtesting.py` | 30 | `coverage = summarize_outcome_coverage(rows)` |
| `automation_scheduler/backtesting.py` | 47 | `"next_required_data": ["settlement_results"],` |
| `automation_scheduler/backtesting.py` | 66 | `"next_required_data": [] if status == "metrics_ready" else ["additional_settlement_results"],` |
| `automation_scheduler/backtesting_engine.py` | 15 | `from .historical_replay import load_historical_rows, replay_rows, summarize_replay_result, write_replay_result` |
| `automation_scheduler/backtesting_engine.py` | 32 | `result_status = str(row.get("result_status", "pending")).lower()` |
| `automation_scheduler/backtesting_engine.py` | 35 | `if result_status == "win":` |
| `automation_scheduler/backtesting_engine.py` | 38 | `elif result_status == "loss":` |
| `automation_scheduler/baseball_data_availability.py` | 43 | `"calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),` |
| `automation_scheduler/baseball_data_availability.py` | 116 | `calibration_allowed = "calibration_outcomes" in available` |
| `automation_scheduler/baseball_data_availability.py` | 128 | `cap_reasons.append("calibration_outcomes_missing")` |
| `automation_scheduler/baseball_data_availability.py` | 139 | `next_data.append("settled_outcomes_by_market_role_context")` |
| `automation_scheduler/baseball_impact_calibration.py` | 22 | `outcomes = _records(source.get("settled_outcomes"))` |
| `automation_scheduler/baseball_impact_calibration.py` | 23 | `explicit = int(safe_float(source.get("matched_outcomes_count"), 0.0) or 0)` |
| `automation_scheduler/baseball_impact_calibration.py` | 25 | `if predictions and outcomes:` |
| `automation_scheduler/baseball_impact_calibration.py` | 26 | `outcome_ids = {str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")) for item in outcomes}` |
| `automation_scheduler/baseball_impact_readiness.py` | 35 | `"real_settled_outcomes_required",` |
| `automation_scheduler/baseball_impact_red_team.py` | 104 | `missing.extend(cal.get("next_required_data") or ["settled_outcomes"])` |
| `automation_scheduler/basketball_player_impact.py` | 194 | `outcome_records: list[dict[str, Any]] \| None = None,` |
| `automation_scheduler/basketball_player_impact.py` | 219 | `calibration = evaluate_basketball_player_impact_calibration(source, outcome_records or [], market_type=source.get("market_type") or source.get("market"))` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 73 | `outcome = str(record.get("outcome") or record.get("result") or "").strip().lower()` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 76 | `hit = outcome in {"hit", "win", "won", "success", "covered", "over_hit", "under_hit"}` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 79 | `elif outcome or record.get("hit") is not None:` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 110 | `"outcome_coverage": round(clamp(sample / max(required_sample_size, 1) * 100.0) / 100.0, 4),` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 60 | `"minutes_outcomes",` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 61 | `"settled_market_outcomes",` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 10 | `player_impact_result: dict[str, Any] \| None = None,` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 15 | `result = player_impact_result if isinstance(player_impact_result, dict) else {}` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 24 | `possession_status = str(result.get("possession_impact", {}).get("possession_impact_status") or result.get("possession_impact_status") or "").lower()` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 25 | `tracking_status = str(result.get("tracking_opportunity", {}).get("tracking_status") or result.get("tracking_status") or "").lower()` |
| `automation_scheduler/bayesian_structural_baseline.py` | 30 | `value = _num(row.get("outcome_value") or row.get("actual") or row.get("return") or row.get("delta"))` |
| `automation_scheduler/bayesian_structural_baseline.py` | 54 | `observed = _num(candidate.get("observed_outcome") or candidate.get("observed_value") or candidate.get("edge_estimate")) or mean` |
| `automation_scheduler/calibration.py` | 8 | `from .outcome_store import load_outcome_records, load_outcome_state, summarize_outcomes` |
| `automation_scheduler/calibration.py` | 13 | `CALIBRATION_SCHEMA_VERSION = f"{SCHEMA_VERSION}.outcome_calibration.v1"` |
| `automation_scheduler/calibration.py` | 14 | `_OUTCOME_KEYS = ("outcome_status", "settlement_status", "final_outcome", "paper_result", "settled_at")` |
| `automation_scheduler/calibration.py` | 55 | `def _normalized_outcome_label(value: Any) -> float \| None:` |
| `automation_scheduler/calibration_collector.py` | 17 | `from .outcome_store import ingest_outcome_records, load_outcome_records` |
| `automation_scheduler/calibration_collector.py` | 29 | `SETTLED_CLASSIFICATIONS = {"settled_yes", "settled_no", "void_or_cancelled"}` |
| `automation_scheduler/calibration_collector.py` | 83 | `"min_target_outcomes": _env_int("KALSHI_CALIBRATION_MIN_TARGET_OUTCOMES", 30),` |
| `automation_scheduler/calibration_collector.py` | 84 | `"good_target_outcomes": _env_int("KALSHI_CALIBRATION_GOOD_TARGET_OUTCOMES", 100),` |
| `automation_scheduler/calibration_tracker.py` | 24 | `def _to_outcome(value: Any) -> float \| None:` |
| `automation_scheduler/calibration_tracker.py` | 44 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/calibration_tracker.py` | 58 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/calibration_tracker.py` | 72 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/candlestick_manifold_detector.py` | 18 | `result = map_market_state(` |
| `automation_scheduler/candlestick_manifold_detector.py` | 25 | `pattern_quality = result.get("normalized_feature_summary", {}).get("pattern_quality_score")` |
| `automation_scheduler/candlestick_manifold_detector.py` | 28 | `reliability = float(result.get("cluster_reliability_score") or 0.0)` |
| `automation_scheduler/candlestick_manifold_detector.py` | 29 | `trap = max(float(result.get("no_trade_trap_score") or 0.0), float(result.get("no_bet_trap_score") or 0.0))` |
| `automation_scheduler/causal_scaffold.py` | 14 | `"outcome_variable": "player_usage_or_prop_line_move",` |
| `automation_scheduler/causal_scaffold.py` | 20 | `"outcome_variable": "total_or_points_prop_hit_rate",` |
| `automation_scheduler/causal_scaffold.py` | 26 | `"outcome_variable": "fake_edge_or_negative_ev_rate",` |
| `automation_scheduler/causal_scaffold.py` | 32 | `"outcome_variable": "momentum_follow_through",` |
| `automation_scheduler/collector_scheduled_runner.py` | 15 | `"persist_outcomes": True,` |
| `automation_scheduler/collector_scheduled_runner.py` | 44 | `"infer_outcomes",` |
| `automation_scheduler/collector_scheduled_runner.py` | 45 | `"inferred_outcomes",` |
| `automation_scheduler/collector_scheduled_runner.py` | 46 | `"allow_inferred_outcomes",` |
| `automation_scheduler/combat_data_availability.py` | 37 | `"calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),` |
| `automation_scheduler/combat_data_availability.py` | 132 | `calibration_allowed = "calibration_outcomes" in available` |
| `automation_scheduler/combat_data_availability.py` | 149 | `next_data.append("settled_combat_market_outcomes")` |
| `automation_scheduler/combat_impact_calibration.py` | 11 | `def _count_outcomes(payload: dict[str, Any]) -> int:` |
| `automation_scheduler/combat_impact_calibration.py` | 12 | `outcomes = payload.get("settled_outcomes")` |
| `automation_scheduler/combat_impact_calibration.py` | 13 | `if isinstance(outcomes, list):` |
| `automation_scheduler/combat_impact_calibration.py` | 14 | `return len(outcomes)` |
| `automation_scheduler/combat_impact_readiness.py` | 39 | `"moneyline": ["fighter_identity", "summary_striking_grappling", "settled_moneyline_outcomes"],` |
| `automation_scheduler/combat_impact_readiness.py` | 40 | `"method_markets": ["finish_path_outcomes", "durability_context", "submission_control_context"],` |
| `automation_scheduler/combat_impact_readiness.py` | 41 | `"round_total_markets": ["round_level_pace_damage", "cardio_decline_context", "finish_timing_outcomes"],` |
| `automation_scheduler/combat_impact_readiness.py` | 43 | `"boxing_props": ["jab_power_punch_tracking", "round_projection", "settled_boxing_prop_outcomes"],` |
| `automation_scheduler/combat_impact_red_team.py` | 96 | `missing.extend(calib.get("next_required_data") or ["settled_combat_market_outcomes"])` |
| `automation_scheduler/combat_phase_control_context.py` | 60 | `if source.get("final_result") and not phase_scores:` |
| `automation_scheduler/combat_phase_control_context.py` | 61 | `no_bet.append("phase_control_not_inferred_from_final_result")` |
| `automation_scheduler/conformal_uncertainty.py` | 21 | `actual = _num(row.get("actual") or row.get("realized_edge") or row.get("outcome"))` |
| `automation_scheduler/conformal_uncertainty.py` | 34 | `minimum_outcomes: int = 50,` |
| `automation_scheduler/conformal_uncertainty.py` | 38 | `if len(residuals) < int(minimum_outcomes):` |
| `automation_scheduler/conformal_uncertainty.py` | 49 | `"conformal_no_bet_reason": "insufficient_calibration_outcomes",` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 8 | `def _outcome_label(row: Mapping[str, Any]) -> str \| None:` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 9 | `value = str(row.get("final_outcome") or row.get("outcome") or row.get("label") or row.get("paper_result") or "").strip().lower()` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 72 | `rows = [row for row in (labeled_records or []) if isinstance(row, Mapping) and _outcome_label(row)]` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 93 | `paired.append((_outcome_label(row), vector_similarity(candidate_vector, vec)))` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 30 | `total_labeled_outcomes: int = 0,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 31 | `outcome_coverage_by_asset_type: dict[str, Any] \| None = None,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 44 | `total_labeled_outcomes=total_labeled_outcomes,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 45 | `outcome_coverage_by_asset_type=outcome_coverage_by_asset_type,` |
| `automation_scheduler/data_availability_tiers.py` | 18 | `0: "TIER_0_OUTCOME_BACKFILL",` |
| `automation_scheduler/data_availability_tiers.py` | 26 | `0: ["schedule", "teams", "event_date", "home_away", "final_score", "final_result", "margin", "total"],` |
| `automation_scheduler/data_availability_tiers.py` | 37 | `0: "outcome_backfill_and_tier_0_calibration_only",` |
| `automation_scheduler/data_availability_tiers.py` | 45 | `-1: "no-call audit for schedule/results/outcome fields",` |
| `automation_scheduler/data_intelligence_registry.py` | 33 | `"calibration_outcome_tracking",` |
| `automation_scheduler/data_intelligence_registry.py` | 74 | `total_labeled_outcomes: int = 0,` |
| `automation_scheduler/data_intelligence_registry.py` | 75 | `outcome_coverage_by_asset_type: Mapping[str, Any] \| None = None,` |
| `automation_scheduler/data_intelligence_registry.py` | 78 | `total_labeled_outcomes=total_labeled_outcomes,` |

## Important Data / Artifact Files
- Data/artifact files found: `250`

| Modified | Size | Tags | Path |
|---|---:|---|---|
| `2026-06-12T18:58:12` | `4927` | `` | `data/data_sources/provider_health/provider_health.json` |
| `2026-06-12T18:58:00` | `2340` | `` | `data/data_sources/nfl_open_data/validated/nflverse_team_stats/latest.json` |
| `2026-06-12T18:58:00` | `2340` | `` | `data/data_sources/nfl_open_data/validated/nflverse_team_stats/items/nflod_tiny_sample_nflverse_team_stats_81453932.json` |
| `2026-06-12T18:58:00` | `2445` | `` | `data/data_sources/nfl_open_data/validated/nflverse_coaching_research/latest.json` |
| `2026-06-12T18:58:00` | `2445` | `` | `data/data_sources/nfl_open_data/validated/nflverse_coaching_research/items/nflod_full_available_backfill_nflverse_coaching_research_e0776ebc.json` |
| `2026-06-12T18:58:00` | `873` | `feature_engineering` | `data/data_sources/nfl_open_data/resume_ledgers/nflverse_team_stats.json` |
| `2026-06-12T18:58:00` | `899` | `feature_engineering` | `data/data_sources/nfl_open_data/resume_ledgers/nflverse_coaching_research.json` |
| `2026-06-12T18:57:54` | `1220` | `model_training,feature_engineering` | `data/manifold/calibration/latest.json` |
| `2026-06-12T18:57:54` | `1220` | `model_training,feature_engineering` | `data/manifold/calibration/2026-06-12.json` |
| `2026-06-12T18:57:48` | `155` | `` | `data/governance_audit/test_audit_record.json` |
| `2026-06-12T18:57:46` | `17421` | `backtesting` | `data/deepseek_profit_lab/disagreements/latest.json` |
| `2026-06-12T18:57:46` | `1469` | `backtesting` | `data/deepseek_profit_lab/disagreements/deepseek_disagreement_b41e0e1c2e615f1a.json` |
| `2026-06-12T18:57:46` | `1469` | `backtesting` | `data/deepseek_profit_lab/disagreements/deepseek_disagreement_396c9231bf8450cb.json` |
| `2026-06-12T18:57:45` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T22_57_45.811737_00_00.json` |
| `2026-06-12T18:57:39` | `108` | `ledger_clv_outcomes` | `data/clv/clv_m2_2026-06-12T22_57_39.057427_00_00.json` |
| `2026-06-12T18:57:39` | `151` | `model_training` | `data/calibration/calibration_m2_2026-06-12T22_57_39.057427_00_00.json` |
| `2026-06-12T18:57:39` | `387` | `bankroll` | `data/bankroll/test_bankroll_redact.json` |
| `2026-06-12T18:57:39` | `359` | `bankroll` | `data/bankroll/test_bankroll.json` |
| `2026-06-12T18:57:39` | `490` | `backtesting` | `data/backtests/replay_m2_2026-06-12T22_57_39.056740_00_00.json` |
| `2026-06-12T18:57:38` | `9092` | `` | `data/system_health/health.json` |
| `2026-06-12T18:57:38` | `1220231` | `feature_engineering,ledger_clv_outcomes` | `data/review_queue/review_queue.json` |
| `2026-06-12T18:57:38` | `1289564` | `feature_engineering,ledger_clv_outcomes` | `data/review_queue/latest.json` |
| `2026-06-12T18:57:38` | `1289564` | `feature_engineering,ledger_clv_outcomes` | `data/review_queue/items/run_4ec8eed57097.json` |
| `2026-06-12T18:57:38` | `2004317` | `` | `data/reports/scheduler_run_run_4ec8eed57097.json` |
| `2026-06-12T18:57:38` | `320826` | `feature_engineering,ledger_clv_outcomes` | `data/paper_ledger/paper_decisions.json` |
| `2026-06-12T18:57:38` | `337077` | `feature_engineering,ledger_clv_outcomes` | `data/paper_ledger/latest.json` |
| `2026-06-12T18:57:38` | `337077` | `feature_engineering,ledger_clv_outcomes` | `data/paper_ledger/items/run_4ec8eed57097.json` |
| `2026-06-12T18:57:38` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T22_57_38.862229_00_00.json` |
| `2026-06-12T18:57:34` | `596950` | `` | `data/snapshots/snapshots/kalshi_snapshot_run_4ec8eed57097.json` |
| `2026-06-12T18:57:34` | `596931` | `` | `data/snapshots/snapshots/kalshi_latest.json` |
| `2026-06-12T18:57:33` | `711` | `` | `data/snapshots/snapshots/sharp_snapshot_run_4ec8eed57097.json` |
| `2026-06-12T18:57:32` | `238` | `` | `data/snapshots/scheduler_runs/run_4ec8eed57097.json` |
| `2026-06-12T18:57:32` | `570745` | `` | `data/data_sources/provider_payload_samples/kalshi_prediction_market_snapshot.json` |
| `2026-06-12T18:57:30` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T22_57_30.908917_00_00.json` |
| `2026-06-12T18:57:12` | `642241` | `feature_engineering,ledger_clv_outcomes` | `data/review_queue/items/run_e7b7d178636b.json` |
| `2026-06-12T18:57:12` | `1172996` | `` | `data/reports/scheduler_run_run_e7b7d178636b.json` |
| `2026-06-12T18:57:12` | `167177` | `feature_engineering,ledger_clv_outcomes` | `data/paper_ledger/items/run_e7b7d178636b.json` |
| `2026-06-12T18:57:12` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T22_57_12.880769_00_00.json` |
| `2026-06-12T18:57:09` | `711` | `` | `data/snapshots/snapshots/sharp_snapshot_run_e7b7d178636b.json` |
| `2026-06-12T18:57:09` | `560879` | `` | `data/snapshots/snapshots/kalshi_snapshot_run_e7b7d178636b.json` |
| `2026-06-12T18:57:07` | `238` | `` | `data/snapshots/scheduler_runs/run_e7b7d178636b.json` |
| `2026-06-12T18:57:04` | `642241` | `feature_engineering,ledger_clv_outcomes` | `data/review_queue/items/run_33b9c252c6ca.json` |
| `2026-06-12T18:57:04` | `1313928` | `` | `data/reports/scheduler_run_run_33b9c252c6ca.json` |
| `2026-06-12T18:57:04` | `167177` | `feature_engineering,ledger_clv_outcomes` | `data/paper_ledger/items/run_33b9c252c6ca.json` |
| `2026-06-12T18:57:04` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T22_57_04.847797_00_00.json` |
| `2026-06-12T18:56:51` | `711` | `` | `data/snapshots/snapshots/sharp_snapshot_run_33b9c252c6ca.json` |
| `2026-06-12T18:56:51` | `560879` | `` | `data/snapshots/snapshots/kalshi_snapshot_run_33b9c252c6ca.json` |
| `2026-06-12T18:56:49` | `238` | `` | `data/snapshots/scheduler_runs/run_33b9c252c6ca.json` |
| `2026-06-12T18:56:47` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T22_56_47.960721_00_00.json` |
| `2026-06-12T15:24:49` | `2340` | `` | `data/data_sources/nfl_open_data/validated/nflverse_team_stats/items/nflod_tiny_sample_nflverse_team_stats_418a5ec3.json` |
| `2026-06-12T15:24:49` | `2445` | `` | `data/data_sources/nfl_open_data/validated/nflverse_coaching_research/items/nflod_full_available_backfill_nflverse_coaching_research_c2c5c9d1.json` |
| `2026-06-12T15:24:35` | `1469` | `backtesting` | `data/deepseek_profit_lab/disagreements/deepseek_disagreement_60a28c9192a25b9c.json` |
| `2026-06-12T15:24:35` | `1469` | `backtesting` | `data/deepseek_profit_lab/disagreements/deepseek_disagreement_2eeb9979e58452ae.json` |
| `2026-06-12T15:24:35` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T19_24_35.025760_00_00.json` |
| `2026-06-12T15:24:29` | `4722844` | `` | `data/reports/scheduler_run_run_9226f0cccdea.json` |
| `2026-06-12T15:24:29` | `108` | `ledger_clv_outcomes` | `data/clv/clv_m2_2026-06-12T19_24_29.117814_00_00.json` |
| `2026-06-12T15:24:29` | `151` | `model_training` | `data/calibration/calibration_m2_2026-06-12T19_24_29.117814_00_00.json` |
| `2026-06-12T15:24:29` | `490` | `backtesting` | `data/backtests/replay_m2_2026-06-12T19_24_29.117814_00_00.json` |
| `2026-06-12T15:24:28` | `3871032` | `feature_engineering,ledger_clv_outcomes` | `data/review_queue/items/run_9226f0cccdea.json` |
| `2026-06-12T15:24:28` | `1012772` | `feature_engineering,ledger_clv_outcomes` | `data/paper_ledger/items/run_9226f0cccdea.json` |
| `2026-06-12T15:24:28` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T19_24_28.785544_00_00.json` |
| `2026-06-12T15:24:16` | `711` | `` | `data/snapshots/snapshots/sharp_snapshot_run_9226f0cccdea.json` |
| `2026-06-12T15:24:16` | `592878` | `` | `data/snapshots/snapshots/kalshi_snapshot_run_9226f0cccdea.json` |
| `2026-06-12T15:24:14` | `238` | `` | `data/snapshots/scheduler_runs/run_9226f0cccdea.json` |
| `2026-06-12T15:24:13` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T19_24_13.193633_00_00.json` |
| `2026-06-12T15:23:58` | `3895762` | `` | `data/reports/scheduler_run_run_614dca3fba6f.json` |
| `2026-06-12T15:23:58` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T19_23_58.175769_00_00.json` |
| `2026-06-12T15:23:57` | `3223667` | `feature_engineering,ledger_clv_outcomes` | `data/review_queue/items/run_614dca3fba6f.json` |
| `2026-06-12T15:23:57` | `842829` | `feature_engineering,ledger_clv_outcomes` | `data/paper_ledger/items/run_614dca3fba6f.json` |
| `2026-06-12T15:23:46` | `711` | `` | `data/snapshots/snapshots/sharp_snapshot_run_614dca3fba6f.json` |
| `2026-06-12T15:23:46` | `585560` | `` | `data/snapshots/snapshots/kalshi_snapshot_run_614dca3fba6f.json` |
| `2026-06-12T15:23:45` | `238` | `` | `data/snapshots/scheduler_runs/run_614dca3fba6f.json` |
| `2026-06-12T15:23:42` | `3223667` | `feature_engineering,ledger_clv_outcomes` | `data/review_queue/items/run_b832d5167563.json` |
| `2026-06-12T15:23:42` | `4038882` | `` | `data/reports/scheduler_run_run_b832d5167563.json` |
| `2026-06-12T15:23:42` | `842829` | `feature_engineering,ledger_clv_outcomes` | `data/paper_ledger/items/run_b832d5167563.json` |
| `2026-06-12T15:23:42` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T19_23_42.778744_00_00.json` |
| `2026-06-12T15:23:31` | `711` | `` | `data/snapshots/snapshots/sharp_snapshot_run_b832d5167563.json` |
| `2026-06-12T15:23:31` | `585560` | `` | `data/snapshots/snapshots/kalshi_snapshot_run_b832d5167563.json` |
| `2026-06-12T15:23:30` | `238` | `` | `data/snapshots/scheduler_runs/run_b832d5167563.json` |
| `2026-06-12T15:23:28` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T19_23_28.090471_00_00.json` |
| `2026-06-12T15:20:24` | `3354597` | `` | `data/reports/scheduler_run_run_ab397f4ebf3b.json` |
| `2026-06-12T15:20:24` | `673732` | `feature_engineering,ledger_clv_outcomes` | `data/paper_ledger/items/run_ab397f4ebf3b.json` |
| `2026-06-12T15:20:24` | `2507` | `model_training` | `data/calibration/calibration_2026-06-12T19_20_24.496555_00_00.json` |
| `2026-06-12T15:20:23` | `2577973` | `feature_engineering,ledger_clv_outcomes` | `data/review_queue/items/run_ab397f4ebf3b.json` |
| `2026-06-12T15:20:12` | `711` | `` | `data/snapshots/snapshots/sharp_snapshot_run_ab397f4ebf3b.json` |
| `2026-06-12T15:20:12` | `559384` | `` | `data/snapshots/snapshots/kalshi_snapshot_run_ab397f4ebf3b.json` |
| `2026-06-12T15:20:10` | `238` | `` | `data/snapshots/scheduler_runs/run_ab397f4ebf3b.json` |
| `2026-06-12T15:17:02` | `1935180` | `feature_engineering,ledger_clv_outcomes` | `data/review_queue/items/run_25533c9ec51a.json` |
| `2026-06-12T15:17:02` | `2681909` | `` | `data/reports/scheduler_run_run_25533c9ec51a.json` |
| `2026-06-12T15:17:02` | `506046` | `feature_engineering,ledger_clv_outcomes` | `data/paper_ledger/items/run_25533c9ec51a.json` |
| `2026-06-12T15:17:02` | `2491` | `model_training` | `data/calibration/calibration_2026-06-12T19_17_02.457356_00_00.json` |
| `2026-06-12T15:16:54` | `711` | `` | `data/snapshots/snapshots/sharp_snapshot_run_25533c9ec51a.json` |
| `2026-06-12T15:16:54` | `602095` | `` | `data/snapshots/snapshots/kalshi_snapshot_run_25533c9ec51a.json` |
| `2026-06-12T15:16:52` | `238` | `` | `data/snapshots/scheduler_runs/run_25533c9ec51a.json` |
| `2026-06-12T15:14:33` | `1473` | `` | `data/performance_reports/perf_default_model_2026-06-12T19_14_33.169451_00_00.json` |
| `2026-06-12T15:14:33` | `40394` | `backtesting` | `data/deepseek_profit_lab/daily_reports/latest.json` |
| `2026-06-12T15:14:33` | `40394` | `backtesting` | `data/deepseek_profit_lab/daily_reports/2026-06-12.json` |
| `2026-06-12T15:14:33` | `116` | `ledger_clv_outcomes` | `data/clv/clv_default_model_2026-06-12T19_14_33.165465_00_00.json` |
| `2026-06-12T15:14:33` | `153` | `model_training` | `data/calibration/calibration_default_model_2026-06-12T19_14_33.165465_00_00.json` |
| `2026-06-12T15:14:33` | `125` | `backtesting` | `data/backtests/replay_default_model_2026-06-12T19_14_33.163472_00_00.json` |

## Test Coverage Signals

### backtest_tests
- Test files with hits: `55`
| File | Line | Match |
|---|---:|---|
| `tests/test_activation_tiers.py` | 7 | `self.assertTrue(can_promote_one_tier('research_only', 'backtest_ready'))` |
| `tests/test_advanced_red_team.py` | 127 | `result = run_advanced_shape_diagnostics(_candidate(), historical_records=_history(), provider="internal_deterministic")` |
| `tests/test_advanced_red_team.py` | 136 | `result = run_topological_red_team(_candidate(), historical_records=_history(40), dependency_available=False)` |
| `tests/test_advanced_red_team.py` | 141 | `result = run_nonlinear_embedding_diagnostics(_candidate(score=70), historical_records=_history(10))` |
| `tests/test_arbitrage_exchange.py` | 10 | `self.assertGreater(result["estimated_roi_percent"], 0)` |
| `tests/test_automation_scheduler_endpoints.py` | 510 | `"execution_simulation": {"execution_desk_status": "simulation_only", "simulated_ticket_created": False},` |
| `tests/test_automation_scheduler_endpoints.py` | 531 | `"automation_scheduler.simulate_institutional_execution",` |
| `tests/test_automation_scheduler_endpoints.py` | 534 | `"status": "simulated",` |
| `tests/test_backtesting.py` | 3 | `from automation_scheduler.backtesting import run_backtesting_scaffold` |
| `tests/test_backtesting.py` | 6 | `class TestBacktesting(unittest.TestCase):` |
| `tests/test_backtesting.py` | 8 | `result = run_backtesting_scaffold([{"provider": "kalshi"}])` |
| `tests/test_backtesting_engine.py` | 6 | `from automation_scheduler.backtesting_engine import generate_backtest_report, run_backtest` |
| `tests/test_backtesting_engine.py` | 9 | `class TestBacktestingEngine(unittest.TestCase):` |
| `tests/test_backtesting_engine.py` | 28 | `result = generate_backtest_report(model_id="m1", rows=rows, base_data_dir=tmp)` |
| `tests/test_backtest_gate.py` | 2 | `from model_governance.backtest_gate import evaluate_backtest_gate` |
| `tests/test_backtest_gate.py` | 5 | `class TestBacktestGate(unittest.TestCase):` |
| `tests/test_backtest_gate.py` | 7 | `r = evaluate_backtest_gate(` |
| `tests/test_baseball_impact_intelligence.py` | 587 | `def test_71_roi_not_emitted_without_real_returns(self):` |
| `tests/test_baseball_impact_intelligence.py` | 589 | `self.assertNotIn("roi_proxy", result)` |
| `tests/test_bet_log.py` | 140 | `def test_performance_summary_calculates_roi_and_yield(self):` |
| `tests/test_bet_log.py` | 153 | `self.assertEqual(summary["roi"], 5)` |
| `tests/test_bet_log.py` | 184 | `self.assertEqual(summary["roi"], 0)` |
| `tests/test_calibration.py` | 160 | `def test_historical_paper_batches_match_after_latest_is_overwritten(self):` |
| `tests/test_calibration_collector.py` | 154 | `def test_collector_preserves_historical_matches_and_daily_matches_calibration(self):` |
| `tests/test_calibration_collector.py` | 159 | `"id": "historical-review",` |
| `tests/test_calibration_collector.py` | 168 | `run_id="close_soon_historical",` |
| `tests/test_collector_scheduled_runner.py` | 143 | `"/api/automation/institutional-lab/execution-desk/simulate",` |
| `tests/test_combat_impact_intelligence.py` | 416 | `def test_092_roi_not_emitted_without_returns(self):` |
| `tests/test_combat_impact_intelligence.py` | 417 | `self.assertNotIn("roi_proxy", evaluate_combat_impact_calibration({"settled_outcomes": [{"hit": True}]}, market_type="moneyline"))` |
| `tests/test_data_availability_tiers.py` | 45 | `self.assertTrue(result["can_backtest"])` |
| `tests/test_data_availability_tiers.py` | 73 | `self.assertFalse(result["can_backtest"])` |
| `tests/test_data_source_endpoints.py` | 177 | `"/api/automation/institutional-lab/execution-desk/simulate",` |
| `tests/test_data_source_research_lanes.py` | 24 | `self.assertIn("historical backfill", requirements)` |
| `tests/test_data_source_research_lanes.py` | 36 | `self.assertIn("historical_backfill_fields_required", task["required_data"])` |
| `tests/test_drawdown_controls.py` | 3 | `from automation_scheduler.drawdown_controls import apply_drawdown_controls` |
| `tests/test_drawdown_controls.py` | 6 | `class DrawdownControlsTests(unittest.TestCase):` |
| `tests/test_drawdown_controls.py` | 7 | `def test_drawdown_8_reduces(self):` |
| `tests/test_ev_line_shopper.py` | 40 | `best["field_scores"] = {"edge_score": 7, "ev_score": 9, "line_value_score": 8, "arbitrage_score": 0, "middle_width_score": 0, "confidence_score": 8, "model_confidence_score": 8, "match_confidence_score": 9, "market_ident` |
| `tests/test_extreme_randomness_diagnostics.py` | 44 | `"historical_sample_size": 40,` |
| `tests/test_field_scorecard.py` | 16 | `"expected_roi_percent": 11,` |
| `tests/test_football_impact_intelligence.py` | 296 | `def test_38_roi_clv_slippage_not_emitted_without_real_price_data(self):` |
| `tests/test_football_impact_intelligence.py` | 298 | `self.assertNotIn("roi_proxy", result)` |
| `tests/test_golf_impact_intelligence.py` | 610 | `def test_082_roi_not_emitted_without_real_returns(self):` |
| `tests/test_golf_impact_intelligence.py` | 612 | `self.assertNotIn("roi_proxy", result)` |
| `tests/test_governance_health.py` | 9 | `self.assertIn("backtest_ready_count", r)` |
| `tests/test_historical_replay.py` | 5 | `from automation_scheduler.historical_replay import (` |
| `tests/test_historical_replay.py` | 6 | `load_historical_rows,` |
| `tests/test_historical_replay.py` | 13 | `class TestHistoricalReplay(unittest.TestCase):` |
| `tests/test_hockey_impact_intelligence.py` | 534 | `result = evaluate_hockey_impact_calibration({"settled_outcomes": [{"hit": True}, {"hit": False}], "historical_predictions": [1, 2]}, sport="icehockey_nhl", market_type="moneyline")` |
| `tests/test_hockey_impact_intelligence.py` | 538 | `def test_082_roi_not_emitted_without_real_returns(self):` |
| `tests/test_hockey_impact_intelligence.py` | 540 | `self.assertNotIn("roi_proxy", result)` |
| `tests/test_institutional_audit_ledger.py` | 18 | `safety_flags={"provider_write": True, "actual_order_submitted": True, "simulated_ticket_created": True},` |
| `tests/test_institutional_cross_asset_lab.py` | 8 | `from automation_scheduler.stake_sizing_simulator import simulate_stake_plan` |
| `tests/test_institutional_cross_asset_lab.py` | 101 | `"estimated_roi_percent": 2.5,` |
| `tests/test_institutional_cross_asset_lab.py` | 106 | `before = simulate_stake_plan(candidate, bankroll=1000, risk_profile="low", max_loss_cap=8)` |
| `tests/test_institutional_cross_asset_reports.py` | 27 | `"execution_simulation": {"execution_desk_status": "simulation_only", "simulated_ticket_created": False},` |
| `tests/test_institutional_execution_desk.py` | 5 | `from automation_scheduler.institutional_execution_desk import ExecutionDeskRejected, simulate_execution, validate_simulation_request` |
| `tests/test_institutional_execution_desk.py` | 37 | `result = simulate_execution(` |
| `tests/test_institutional_execution_desk.py` | 44 | `"human_command": "simulate_only",` |
| `tests/test_institutional_performance_attribution.py` | 19 | `"drawdowns": [-0.04, -0.02, -0.01],` |

### training_tests
- Test files with hits: `162`
| File | Line | Match |
|---|---:|---|
| `tests/test_activation_tiers.py` | 2 | `from model_governance.activation_tiers import default_activation_tier, can_promote_one_tier, tier_allows_active_scoring` |
| `tests/test_advanced_red_team.py` | 67 | `def _calibration(count=60, residual=0.04):` |
| `tests/test_advanced_red_team.py` | 171 | `result = run_conformal_uncertainty(_candidate(), calibration_records=_calibration(5))` |
| `tests/test_advanced_red_team.py` | 203 | `calibration_records=_calibration(5),` |
| `tests/test_afl_model_activation.py` | 5 | `import multi_sport_model_registry as registry` |
| `tests/test_afl_model_activation.py` | 6 | `from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot` |
| `tests/test_afl_model_activation.py` | 9 | `MODEL_NAME = "afl_clearance_inside50_scoring_shot_monte_carlo_model"` |
| `tests/test_alert_gate.py` | 2 | `from model_governance.alert_gate import evaluate_alert_gate` |
| `tests/test_analyze_event.py` | 8 | `from src.api.schemas.betting_actions import AnalyzeEventRequest, AnalyzeEventResponse, PriceEventRequest, ModelProbabilityRequest, EvaluateLinesRequest` |
| `tests/test_analyze_event.py` | 17 | `def classify_model_level(self, sport):` |
| `tests/test_analyze_event.py` | 63 | `def _model_result(row, final_probability=0.55, probability_type="blended_market_and_projection"):` |
| `tests/test_arbitrage_detector.py` | 19 | `self.assertGreater(result["min_profit"], 0)` |
| `tests/test_automation_scheduler_endpoints.py` | 44 | `def test_calibration_endpoint_compact_default(self):` |
| `tests/test_automation_scheduler_endpoints.py` | 45 | `r = self.client.get('/api/automation/calibration')` |
| `tests/test_automation_scheduler_endpoints.py` | 167 | `def test_calibration_collector_endpoint_compact_default(self):` |
| `tests/test_backtesting.py` | 23 | `self.assertEqual(result["status"], "partial_calibration")` |
| `tests/test_backtesting.py` | 33 | `self.assertEqual(result["status"], "partial_calibration")` |
| `tests/test_backtesting_engine.py` | 19 | `"model_probability": 0.57,` |
| `tests/test_backtesting_engine.py` | 28 | `result = generate_backtest_report(model_id="m1", rows=rows, base_data_dir=tmp)` |
| `tests/test_backtesting_engine.py` | 34 | `self.assertEqual(payload["model_id"], "m1")` |
| `tests/test_backtest_gate.py` | 2 | `from model_governance.backtest_gate import evaluate_backtest_gate` |
| `tests/test_badminton_model_activation.py` | 5 | `import multi_sport_model_registry as registry` |
| `tests/test_badminton_model_activation.py` | 6 | `from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot` |
| `tests/test_badminton_model_activation.py` | 9 | `MODEL_NAME = "badminton_serve_return_rally_momentum_shuttle_monte_carlo_model"` |
| `tests/test_baseball_impact_intelligence.py` | 10 | `from automation_scheduler.baseball_impact_calibration import evaluate_baseball_impact_calibration` |
| `tests/test_baseball_impact_intelligence.py` | 180 | `"calibration_context": {"matched_outcomes_count": 0},` |
| `tests/test_baseball_impact_intelligence.py` | 506 | `def test_59_narrative_overfit_risk_downgrades_weak_incentive_claims(self):` |
| `tests/test_basketball_player_impact.py` | 8 | `from automation_scheduler.basketball_player_impact_calibration import evaluate_basketball_player_impact_calibration` |
| `tests/test_basketball_player_impact.py` | 132 | `"calibration_error": 0.07,` |
| `tests/test_basketball_player_impact.py` | 133 | `"profit": 1.0 if i % 3 != 0 else -1.0,` |
| `tests/test_bet_log.py` | 36 | `return bet_log.create_bet_log_entry(payload.model_dump(exclude_none=True))` |
| `tests/test_bet_log.py` | 110 | `def test_log_result_calculates_win_profit(self):` |
| `tests/test_bet_log.py` | 118 | `self.assertEqual(updated["profit_loss"], 30)` |
| `tests/test_calibration.py` | 4 | `from automation_scheduler.calibration import (` |
| `tests/test_calibration.py` | 5 | `build_calibration_report,` |
| `tests/test_calibration.py` | 8 | `run_calibration_scaffold,` |
| `tests/test_calibration_collector.py` | 8 | `from automation_scheduler.calibration import build_calibration_report` |
| `tests/test_calibration_collector.py` | 9 | `from automation_scheduler.calibration_collector import _normalize_records, _select_candidates, collector_policy_from_env, run_collector_cycle, write_daily_report` |
| `tests/test_calibration_collector.py` | 36 | `class TestCalibrationCollector(unittest.TestCase):` |
| `tests/test_calibration_gate.py` | 2 | `from model_governance.calibration_gate import evaluate_calibration_gate` |
| `tests/test_calibration_gate.py` | 5 | `class TestCalibrationGate(unittest.TestCase):` |
| `tests/test_calibration_gate.py` | 7 | `r = evaluate_calibration_gate(` |
| `tests/test_calibration_tracker.py` | 3 | `from automation_scheduler.calibration_tracker import (` |
| `tests/test_calibration_tracker.py` | 6 | `calculate_expected_calibration_error,` |
| `tests/test_calibration_tracker.py` | 12 | `class TestCalibrationTracker(unittest.TestCase):` |
| `tests/test_call_of_duty_esports_model_activation.py` | 5 | `import multi_sport_model_registry as registry` |
| `tests/test_call_of_duty_esports_model_activation.py` | 6 | `from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot` |
| `tests/test_call_of_duty_esports_model_activation.py` | 10 | `data = deepcopy(registry.get_sport_model_config("call_of_duty")["screenshot_alias_test_payload"]["input_stats"])` |
| `tests/test_champion_challenger.py` | 2 | `from model_governance.champion_challenger import compare_champion_challenger` |
| `tests/test_champion_challenger.py` | 6 | `r = compare_champion_challenger(champion={'sample_size':200,'calibration':80,'risk_adjusted':80,'settlement_failures':0,'liquidity_failures':0}, challenger={'sample_size':200,'calibration':90,'risk_adjusted':90,'settleme` |
| `tests/test_clv_tracker.py` | 7 | `summarize_clv_by_model,` |
| `tests/test_clv_tracker.py` | 22 | `def test_summarize_by_model(self):` |
| `tests/test_clv_tracker.py` | 23 | `summary = summarize_clv_by_model(` |
| `tests/test_collector_scheduled_runner.py` | 30 | `response = self.client.post("/api/automation/calibration-collector/scheduled-run", json={})` |
| `tests/test_collector_scheduled_runner.py` | 37 | `"/api/automation/calibration-collector/scheduled-run",` |
| `tests/test_collector_scheduled_runner.py` | 48 | `"automation_scheduler.run_automation_calibration_collector_scheduled",` |
| `tests/test_college_football_model_activation.py` | 6 | `from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot` |
| `tests/test_college_football_model_activation.py` | 89 | `class TestCollegeFootballModelActivation(unittest.TestCase):` |
| `tests/test_college_football_model_activation.py` | 91 | `return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))` |
| `tests/test_combat_impact_intelligence.py` | 9 | `from automation_scheduler.combat_impact_calibration import evaluate_combat_impact_calibration` |
| `tests/test_combat_impact_intelligence.py` | 111 | `"calibration_context": {"matched_outcomes_count": 0},` |
| `tests/test_combat_impact_intelligence.py` | 283 | `class TestCombatContextMarketCalibrationRedTeam(unittest.TestCase):` |
| `tests/test_combat_sports_model_activation.py` | 5 | `from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot` |
| `tests/test_combat_sports_model_activation.py` | 101 | `class TestCombatSportsModelActivation(unittest.TestCase):` |
| `tests/test_combat_sports_model_activation.py` | 103 | `return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**sport_payload(**extra))))` |
| `tests/test_cricket_model_activation.py` | 6 | `from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot` |
| `tests/test_cricket_model_activation.py` | 86 | `class TestCricketModelActivation(unittest.TestCase):` |
| `tests/test_cricket_model_activation.py` | 88 | `return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))` |
| `tests/test_cross_book_gate.py` | 2 | `from model_governance.cross_book_gate import evaluate_cross_book_gate` |
| `tests/test_cs2_esports_model_activation.py` | 5 | `import multi_sport_model_registry as registry` |
| `tests/test_cs2_esports_model_activation.py` | 6 | `from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot` |
| `tests/test_cs2_esports_model_activation.py` | 10 | `data = deepcopy(registry.get_sport_model_config("cs2")["screenshot_alias_test_payload"]["input_stats"])` |
| `tests/test_darts_model_activation.py` | 5 | `import multi_sport_model_registry as registry` |
| `tests/test_darts_model_activation.py` | 6 | `from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot` |
| `tests/test_darts_model_activation.py` | 9 | `MODEL_NAME = "darts_checkout_scoring_pressure_leg_set_monte_carlo_model"` |
| `tests/test_data_availability_tiers.py` | 8 | `build_prediction_calibration_metadata,` |
| `tests/test_data_availability_tiers.py` | 58 | `self.assertNotEqual(tier1["calibration_bucket"], tier3["calibration_bucket"])` |
| `tests/test_data_availability_tiers.py` | 63 | `self.assertTrue(result["can_train_baseline"])` |

### bankroll_tests
- Test files with hits: `71`
| File | Line | Match |
|---|---:|---|
| `tests/test_afl_model_activation.py` | 45 | `"bankroll": 1000,` |
| `tests/test_afl_model_activation.py` | 46 | `"unit_size": 25,` |
| `tests/test_afl_model_activation.py` | 71 | `"bankroll": 1000,` |
| `tests/test_analyze_event.py` | 96 | `bankroll=1000,` |
| `tests/test_analyze_event.py` | 97 | `unit_size=10,` |
| `tests/test_analyze_event.py` | 99 | `max_stake_pct=0.05,` |
| `tests/test_arbitrage_detector.py` | 13 | `total_stake=100,` |
| `tests/test_automation_scheduler_endpoints.py` | 444 | `"repeated_model_mistakes": [],` |
| `tests/test_backtesting_engine.py` | 24 | `"recommended_stake_percent": 1.2,` |
| `tests/test_badminton_model_activation.py` | 30 | `"odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,` |
| `tests/test_badminton_model_activation.py` | 48 | `"bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",` |
| `tests/test_badminton_model_activation.py` | 79 | `self.assertEqual(response["suggested_stake"], 0)` |
| `tests/test_bankroll_state.py` | 4 | `from automation_scheduler.bankroll_state import default_bankroll_state, load_bankroll_state, save_bankroll_state` |
| `tests/test_bankroll_state.py` | 7 | `class BankrollStateTests(unittest.TestCase):` |
| `tests/test_bankroll_state.py` | 9 | `s = default_bankroll_state(2000)` |
| `tests/test_basketball_player_impact.py` | 153 | `sportsbook_bet_payload={"stake": 100, "selection": "over"},` |
| `tests/test_basketball_player_impact.py` | 162 | `self.assertNotIn("'stake': 100", rendered)` |
| `tests/test_bet_log.py` | 22 | `"stake": 25,` |
| `tests/test_bet_log.py` | 23 | `"unit_size": 25,` |
| `tests/test_bet_log.py` | 24 | `"bankroll_at_bet": 1000,` |
| `tests/test_call_of_duty_esports_model_activation.py` | 39 | `"bankroll": 1000,` |
| `tests/test_call_of_duty_esports_model_activation.py` | 40 | `"unit_size": 25,` |
| `tests/test_call_of_duty_esports_model_activation.py` | 66 | `"bankroll": 1000,` |
| `tests/test_college_football_model_activation.py` | 83 | `"bankroll": 1000, "unit_size": 25, "risk_profile": "moderate", "input_stats": cfb_inputs(),` |
| `tests/test_college_football_model_activation.py` | 98 | `"bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",` |
| `tests/test_college_football_model_activation.py` | 113 | `self.assertEqual(response["suggested_stake"], 0)` |
| `tests/test_combat_impact_intelligence.py` | 363 | `def test_076_title_stakes_if_supplied(self):` |
| `tests/test_combat_sports_model_activation.py` | 92 | `"bankroll": 1000,` |
| `tests/test_combat_sports_model_activation.py` | 93 | `"unit_size": 25,` |
| `tests/test_combat_sports_model_activation.py` | 115 | `"bankroll": 1000,` |
| `tests/test_cricket_model_activation.py` | 78 | `"book": "Manual", "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",` |
| `tests/test_cricket_model_activation.py` | 95 | `"book": "Manual", "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",` |
| `tests/test_cricket_model_activation.py` | 111 | `self.assertEqual(response["suggested_stake"], 0)` |
| `tests/test_cs2_esports_model_activation.py` | 39 | `"bankroll": 1000,` |
| `tests/test_cs2_esports_model_activation.py` | 40 | `"unit_size": 25,` |
| `tests/test_cs2_esports_model_activation.py` | 66 | `"bankroll": 1000,` |
| `tests/test_darts_model_activation.py` | 36 | `"bankroll": 1000,` |
| `tests/test_darts_model_activation.py` | 37 | `"unit_size": 25,` |
| `tests/test_darts_model_activation.py` | 62 | `"bankroll": 1000,` |
| `tests/test_deepseek_profit_lab.py` | 103 | `"repeated_model_mistakes": [],` |
| `tests/test_deepseek_profit_lab.py` | 175 | `sportsbook_bet_payload={"stake": 100},` |
| `tests/test_deepseek_profit_lab.py` | 235 | `_valid_review(bet_slip={"stake": 25}),` |
| `tests/test_dota2_esports_model_activation.py` | 39 | `"bankroll": 1000,` |
| `tests/test_dota2_esports_model_activation.py` | 40 | `"unit_size": 25,` |
| `tests/test_dota2_esports_model_activation.py` | 66 | `"bankroll": 1000,` |
| `tests/test_drawdown_controls.py` | 9 | `self.assertAlmostEqual(res["adjusted_stake_fraction"], 0.03, places=6)` |
| `tests/test_drawdown_controls.py` | 13 | `self.assertAlmostEqual(res["adjusted_stake_fraction"], 0.02, places=6)` |
| `tests/test_drawdown_controls.py` | 17 | `self.assertEqual(res["adjusted_stake_fraction"], 0.0)` |
| `tests/test_evaluate_lines.py` | 24 | `"bankroll": 1000,` |
| `tests/test_evaluate_lines.py` | 25 | `"unit_size": 25,` |
| `tests/test_evaluate_lines.py` | 42 | `self.assertEqual(out["results"][0]["suggested_stake"], 0)` |
| `tests/test_exposure_limits.py` | 3 | `from automation_scheduler.exposure_limits import (` |
| `tests/test_exposure_limits.py` | 4 | `apply_all_exposure_caps,` |
| `tests/test_exposure_limits.py` | 5 | `cap_daily_exposure,` |
| `tests/test_football_impact_intelligence.py` | 330 | `team_context={"team": "A", "order_payload": {"side": "buy"}, "bet_slip": {"stake": 100}},` |
| `tests/test_football_impact_intelligence.py` | 334 | `self.assertNotIn("stake", rendered)` |
| `tests/test_football_impact_intelligence.py` | 523 | `team_context={"team": "A", "sportsbook_ticket": {"stake": 500}, "raw_response": {"secret": "drop"}},` |
| `tests/test_formula_1_model_activation.py` | 87 | `"odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,` |
| `tests/test_formula_1_model_activation.py` | 104 | `"odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,` |
| `tests/test_formula_1_model_activation.py` | 120 | `self.assertEqual(response["suggested_stake"], 0)` |
| `tests/test_formula_e_model_activation.py` | 41 | `"bankroll": 1000,` |
| `tests/test_formula_e_model_activation.py` | 42 | `"unit_size": 25,` |
| `tests/test_formula_e_model_activation.py` | 67 | `"bankroll": 1000,` |
| `tests/test_golf_impact_intelligence.py` | 128 | `"wind_exposure": "moderate",` |
| `tests/test_golf_model_activation.py` | 64 | `"bankroll": 1000,` |
| `tests/test_golf_model_activation.py` | 65 | `"unit_size": 25,` |
| `tests/test_golf_model_activation.py` | 86 | `"bankroll": 1000,` |
| `tests/test_handball_model_activation.py` | 30 | `"odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,` |
| `tests/test_handball_model_activation.py` | 47 | `"odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,` |
| `tests/test_handball_model_activation.py` | 78 | `self.assertEqual(response["suggested_stake"], 0)` |
| `tests/test_hockey_impact_intelligence.py` | 629 | `safe = redact_and_limit_payload({"bet_slip": {"stake": 10}, "slip_payload": {"stake": 10}})` |
| `tests/test_indycar_model_activation.py` | 33 | `self.assertEqual(response["suggested_stake"], 0)` |
| `tests/test_indycar_model_activation.py` | 39 | `self.assertEqual(response["suggested_stake"], 0)` |
| `tests/test_indycar_model_activation.py` | 78 | `self.assertEqual(response["suggested_stake"], 0)` |
| `tests/test_institutional_credit_risk_models.py` | 21 | `"exposure": 1000000,` |

### ledger_outcome_tests
- Test files with hits: `84`
| File | Line | Match |
|---|---:|---|
| `tests/test_advanced_red_team.py` | 48 | `"outcome_value": 0.01 * ((i % 3) - 1),` |
| `tests/test_advanced_red_team.py` | 59 | `"outcome": "yes" if i % 2 else "no",` |
| `tests/test_advanced_red_team.py` | 61 | `"final_outcome": "win" if i % 2 else "loss",` |
| `tests/test_arbitrage_risk_filters.py` | 7 | `def test_stale_price_and_settlement_mismatch_block(self):` |
| `tests/test_arbitrage_risk_filters.py` | 15 | `self.assertIn("settlement_mismatch", result["blockers"])` |
| `tests/test_automation_scheduler_endpoints.py` | 49 | `self.assertIn('paper_decisions_count', p)` |
| `tests/test_automation_scheduler_endpoints.py` | 50 | `self.assertIn('outcome_records_count', p)` |
| `tests/test_automation_scheduler_endpoints.py` | 56 | `def test_outcome_endpoints_compact_default(self):` |
| `tests/test_backtesting.py` | 7 | `def test_insufficient_without_outcomes(self):` |
| `tests/test_backtesting.py` | 11 | `def test_computed_with_outcomes(self):` |
| `tests/test_backtesting.py` | 12 | `result = run_backtesting_scaffold([{"provider": "kalshi", "final_outcome": 1}, {"provider": "sharp", "final_outcome": 0}])` |
| `tests/test_backtest_gate.py` | 17 | `positive_clv_rate=0.6,` |
| `tests/test_baseball_impact_intelligence.py` | 180 | `"calibration_context": {"matched_outcomes_count": 0},` |
| `tests/test_baseball_impact_intelligence.py` | 575 | `def test_68_no_labeled_outcomes_returns_insufficient_data(self):` |
| `tests/test_baseball_impact_intelligence.py` | 576 | `result = evaluate_baseball_impact_calibration({"matched_outcomes_count": 0}, sport="baseball_mlb", market_type="total", role="TEAM_OFFENSE", data_tier=2)` |
| `tests/test_basketball_player_impact.py` | 198 | `high_tracking = run_basketball_player_impact(candidate(lineup_net_rating=0, defensive_matchup_rating=50), outcome_records=settled_records())` |
| `tests/test_basketball_player_impact.py` | 215 | `outcome_records=settled_records(),` |
| `tests/test_basketball_player_impact.py` | 217 | `low_blowout = run_basketball_player_impact(candidate(blowout_risk=5), outcome_records=settled_records())` |
| `tests/test_bet_log.py` | 169 | `def test_clv_report_calculates_clv_when_closing_odds_exist(self):` |
| `tests/test_bet_log.py` | 172 | `report = bet_log.get_clv_report(entries)` |
| `tests/test_bet_log.py` | 175 | `self.assertGreater(report["bets"][0]["clv_percent"], 0)` |
| `tests/test_broker_quality_scoring.py` | 10 | `"broker_name": "Paper Broker",` |
| `tests/test_broker_quality_scoring.py` | 20 | `"paper_or_sandbox_support": True,` |
| `tests/test_calibration.py` | 6 | `load_outcome_records,` |
| `tests/test_calibration.py` | 7 | `match_outcomes_to_paper_decisions,` |
| `tests/test_calibration.py` | 9 | `summarize_outcome_coverage,` |
| `tests/test_calibration_collector.py` | 11 | `from automation_scheduler.outcome_store import ingest_outcome_records, load_outcome_records` |
| `tests/test_calibration_collector.py` | 12 | `from automation_scheduler.paper_decision_ledger import persist_paper_decisions_for_review_items` |
| `tests/test_calibration_collector.py` | 53 | `persist_outcomes=False,` |
| `tests/test_champion_challenger.py` | 5 | `def test_outcomes(self):` |
| `tests/test_champion_challenger.py` | 6 | `r = compare_champion_challenger(champion={'sample_size':200,'calibration':80,'risk_adjusted':80,'settlement_failures':0,'liquidity_failures':0}, challenger={'sample_size':200,'calibration':90,'risk_adjusted':90,'settleme` |
| `tests/test_clv_tracker.py` | 3 | `from automation_scheduler.clv_tracker import (` |
| `tests/test_clv_tracker.py` | 4 | `calculate_clv_for_american_odds,` |
| `tests/test_clv_tracker.py` | 5 | `calculate_positive_clv_rate,` |
| `tests/test_collector_scheduled_runner.py` | 54 | `"persist_outcomes": True,` |
| `tests/test_collector_scheduled_runner.py` | 132 | `self.assertTrue(kwargs["persist_outcomes"])` |
| `tests/test_combat_impact_intelligence.py` | 111 | `"calibration_context": {"matched_outcomes_count": 0},` |
| `tests/test_combat_impact_intelligence.py` | 407 | `def test_089_no_outcomes_insufficient_data(self):` |
| `tests/test_combat_impact_intelligence.py` | 411 | `self.assertTrue(evaluate_combat_impact_calibration({"matched_outcomes_count": 12}, market_type="moneyline")["insufficient_sample"])` |
| `tests/test_data_availability_tiers.py` | 44 | `self.assertEqual(result["data_availability_tier"], "TIER_0_OUTCOME_BACKFILL")` |
| `tests/test_data_intelligence_stack.py` | 23 | `registry = build_data_intelligence_registry(total_labeled_outcomes=0)` |
| `tests/test_data_intelligence_stack.py` | 32 | `registry = build_model_maturity_registry(total_labeled_outcomes=0)` |
| `tests/test_data_intelligence_stack.py` | 44 | `"outcome_coverage",` |
| `tests/test_data_lineage.py` | 14 | `self.assertIn("settlement_rule_status", r)` |
| `tests/test_data_paths.py` | 14 | `get_outcomes_dir,` |
| `tests/test_data_paths.py` | 15 | `get_paper_ledger_dir,` |
| `tests/test_data_paths.py` | 27 | `self.assertEqual(get_runtime_data_path("outcomes"), Path(tmp).resolve() / "outcomes")` |
| `tests/test_data_source_endpoints.py` | 193 | `"persist_outcomes": False,` |
| `tests/test_data_source_endpoints.py` | 201 | `json={"dry_run": True, "persist_outcomes": False, "max_new_contracts": 1},` |
| `tests/test_data_source_research_lanes.py` | 16 | `def test_task_requirements_cover_access_terms_limits_mapping_and_outcomes(self):` |
| `tests/test_data_source_research_lanes.py` | 23 | `self.assertIn("final outcome", requirements)` |
| `tests/test_data_source_research_lanes.py` | 35 | `self.assertIn("outcome_fields_required", task["required_data"])` |
| `tests/test_deepseek_data_pull_check_contract.py` | 14 | `from automation_scheduler.prediction_market_outcome_candidates import (` |
| `tests/test_deepseek_data_pull_check_contract.py` | 16 | `evaluate_outcome_evidence,` |
| `tests/test_deepseek_data_pull_check_contract.py` | 17 | `run_tiny_read_only_settlement_check,` |
| `tests/test_deepseek_profit_lab.py` | 74 | `"missing_inputs": ["settlement_sample"],` |
| `tests/test_deepseek_profit_lab.py` | 78 | `"next_data_to_collect": ["settled_outcomes"],` |
| `tests/test_deepseek_profit_lab.py` | 104 | `"recommended_next_data_to_collect": ["outcomes"],` |
| `tests/test_deepseek_reviewer.py` | 49 | `result = run_deepseek_review(collector_cycle_report={"matched_outcomes_count": 0})` |
| `tests/test_derived_feature_backfill_report.py` | 101 | `def test_market_and_prediction_outcome_features_are_explicit(self):` |
| `tests/test_derived_feature_backfill_report.py` | 106 | `{"provider": "kalshi", "ticker": "KXYES", "implied_probability": 0.57, "final_outcome": "yes"},` |
| `tests/test_derived_feature_backfill_report.py` | 107 | `{"provider": "kalshi", "ticker": "KXNO", "implied_probability": 0.42, "final_outcome": "no"},` |
| `tests/test_ev_line_shopper.py` | 40 | `best["field_scores"] = {"edge_score": 7, "ev_score": 9, "line_value_score": 8, "arbitrage_score": 0, "middle_width_score": 0, "confidence_score": 8, "model_confidence_score": 8, "match_confidence_score": 9, "market_ident` |
| `tests/test_football_impact_intelligence.py` | 284 | `def test_35_no_labeled_outcomes_returns_insufficient_data(self):` |
| `tests/test_football_impact_intelligence.py` | 289 | `result = evaluate_football_impact_calibration({"matched_outcomes_count": 10}, sport="americanfootball_nfl", market_type="spread", role="QB", data_tier=3)` |
| `tests/test_football_impact_intelligence.py` | 292 | `def test_37_real_labeled_outcomes_enable_partial_calibration(self):` |
| `tests/test_golf_impact_intelligence.py` | 200 | `"matched_outcomes_count": 0,` |
| `tests/test_golf_impact_intelligence.py` | 595 | `report = _full_report(market_type="outright_winner", calibration_context={"matched_outcomes_count": 0})` |
| `tests/test_golf_impact_intelligence.py` | 598 | `def test_079_no_labeled_outcomes_returns_insufficient_data(self):` |
| `tests/test_governance_config.py` | 11 | `self.assertTrue(cfg['paper_execution_only'])` |
| `tests/test_hockey_impact_intelligence.py` | 176 | `result = build_hockey_impact_diagnostics(team_context=_team_context(), calibration_context={"matched_outcomes_count": 0})` |
| `tests/test_hockey_impact_intelligence.py` | 481 | `calibration_context={"matched_outcomes_count": 0},` |
| `tests/test_hockey_impact_intelligence.py` | 525 | `def test_079_no_labeled_outcomes_returns_insufficient_data(self):` |

## Entry Point / Function Inventory
- Interesting Python files: `652`

| File | Classes | Functions sample |
|---|---|---|
| `api_server.py` | `` | `_verify_runtime_routes` |
| `asian_markets.py` | `AsianHandicapSettlement` | `hong_kong_to_decimal, malaysian_to_decimal, indonesian_to_decimal, decimal_to_hong_kong, decimal_to_malaysian, decimal_to_indonesian, american_to_hong_kong, quarter_line_split, asian_handicap_push_half_probabilities, compare_asian_handicap_to_american_spread, asian_total_quarter_split, asian_market_lead_lag_score` |
| `bet_decision_engine.py` | `` | `_normalize_selection, _normalize_market, find_two_way_counterpart, no_vig_probability_for_line, risk_grade_from_kelly, kelly_fraction_multiplier, decision_label, reason_text, evaluate_lines_payload` |
| `bet_log.py` | `` | `_now_iso, _log_path, _to_float, _to_int, _normalize_confidence, _american_to_decimal, _implied_probability, _is_worse_price, calculate_profit_loss, calculate_clv_percent, _resolve_error_type, create_bet_log_entry` |
| `config.py` | `ConfigError, Config` | `get_required_env, load_config, __init__` |
| `full_board_engine.py` | `` | `_identity, _same_market_selection, _remove_confirmed_selection_no_bets, build_full_board_preview` |
| `kalshi_client.py` | `` | `_json_response, _get, get_kalshi_market, get_kalshi_orderbook, _extract_price, _extract_prices, get_kalshi_market_snapshot` |
| `logbook_engine.py` | `` | `build_logbook_ready_row` |
| `logger_setup.py` | `` | `setup_logger` |
| `main.py` | `` | `utc_now, no_data_response, provider_error_response, get_configured_action_key, extract_bearer_token, require_action_key, resolve_sport_key, stock_data` |
| `market_pricing.py` | `` | `book_hold_from_american_pair, book_hold_from_american_n_way, best_price_american, worst_price_american, average_implied_probability, median_implied_probability, market_spread_implied, no_vig_consensus_probability, sharp_book_consensus_probability, soft_book_stale_line_flag, opening_vs_current_clv_implied_change_pct, current_vs_projected_close_delta` |
| `model_blender.py` | `` | `blend_probabilities, confidence_score` |
| `model_probability.py` | `IndependentInputs, ModelProbabilityResult` | `calculate_data_quality_score, calculate_confidence_score, get_confidence_grade, apply_adjustment_caps, blend_probabilities, create_probability_response, __init__, get_active_inputs, get_missing_inputs, get_adjustment_values, __init__` |
| `multi_sport_model_registry.py` | `` | `_component, _props_registry_entry, _officials_module, _official_input_value, _official_inputs_present, _official_affected_markets, _officiating_cap, _explicit_officiating_adjustment, build_officiating_analysis, _sport, normalize_sport_key, _validate_registry` |
| `parlay_engine.py` | `` | `parlay_decimal_odds, parlay_implied_probability, parlay_independent_win_probability, parlay_correlation_adjusted_probability, parlay_ev, parlay_kelly, same_game_parlay_risk_warning, positive_correlation_flag, negative_correlation_flag, hidden_duplicate_exposure_flag, no_bet_parlay_trap_flag` |
| `quant_engine.py` | `` | `_validate_american_odds, _validate_probability, american_to_decimal, american_to_implied_probability, implied_probability_from_american, decimal_to_american, probability_to_fair_american, expected_value_per_unit, expected_value_dollars, kelly_fraction, suggested_stake, suggested_bet_size` |
| `risk_engine.py` | `` | `bankroll_percentage_risked, exposure_single_bet, exposure_daily, exposure_by_key, correlation_group_exposure, max_loss_correlated_bets, drawdown_tracker, risk_of_ruin_estimate, risk_profile_settings, confidence_adjusted_stake, risk_adjusted_stake, suggested_stake` |
| `screenshot_intake.py` | `` | `_present, _identity, _confirmed_logbook_row, _collect_confirmed_rows, _remove_confirmed_selection_no_bets, _remove_stale_no_bet_logbook_rows, _cleanup_confirmed_selection_no_bets, parse_ticket, analyze_screenshot_ticket, collect_from_container, same_confirmed_selection` |
| `sharp_client.py` | `` | `_safe_json, _provider_response, get_sharp_active_events, get_sharp_event_odds` |
| `automation_scheduler/advanced_red_team_provider_policy.py` | `` | `_env_bool, _timeout_seconds, get_advanced_red_team_config, provider_not_allowed_response, evaluate_advanced_red_team_provider` |
| `automation_scheduler/advanced_red_team_report.py` | `` | `_root, _atomic_write, _reason_counts, write_advanced_red_team_report, write_advanced_diagnostics, load_advanced_red_team_latest, build_advanced_red_team_report` |
| `automation_scheduler/advanced_shape_diagnostics.py` | `` | `_num, _safe_flags, get_advanced_diagnostic_registry, _vector_from_record, _feature_names, euclidean_distance, vector_similarity, vector_context, run_graph_density_diagnostics, _series_from_inputs, run_advanced_shape_diagnostics` |
| `automation_scheduler/ai_provider_security.py` | `` | `_timeout_seconds, get_ai_provider_config, _rejected_response, evaluate_ai_provider` |
| `automation_scheduler/alert_engine.py` | `` | `contains_banned_language, sanitize_reason, build_alert, generate_alert_candidates` |
| `automation_scheduler/arbitrage_detector.py` | `` | `detect_arbitrage` |
| `automation_scheduler/audit_ledger.py` | `` | `_audit_dir, _atomic_write_json, _read_json, _existing_items, append_security_event, load_security_audit_records` |
| `automation_scheduler/backtesting.py` | `` | `_group_counts, _reason_counts, run_backtesting_scaffold` |
| `automation_scheduler/backtesting_engine.py` | `` | `_to_float, _paper_rows_from_replay_rows, compare_expected_vs_realized, run_backtest, run_paper_summary, generate_backtest_report` |
| `automation_scheduler/balance_sheet_risk.py` | `` | `_num, _clamp, _ratio, _sum_present, _risk_bucket, evaluate_balance_sheet` |
| `automation_scheduler/bankroll_state.py` | `` | `_root, _redact, default_bankroll_state, save_bankroll_state, load_bankroll_state` |
| `automation_scheduler/baseball_availability_context.py` | `` | `_injury_risk, evaluate_baseball_availability_context` |
| `automation_scheduler/baseball_batter_impact.py` | `` | `evaluate_baseball_batter_impact` |
| `automation_scheduler/baseball_bullpen_context.py` | `` | `_unavailable_count, evaluate_baseball_bullpen_context` |
| `automation_scheduler/baseball_data_availability.py` | `` | `_merge, evaluate_baseball_data_availability` |
| `automation_scheduler/baseball_defense_baserunning_context.py` | `` | `evaluate_baseball_defense_baserunning_context` |
| `automation_scheduler/baseball_impact_calibration.py` | `` | `_records, evaluate_baseball_impact_calibration` |
| `automation_scheduler/baseball_impact_common.py` | `` | `normalize_baseball_sport, normalize_baseball_market, normalize_baseball_role, safe_float, boolish, clamp, score_from_range, score_centered, percent_score, weighted_average, present_fields, missing_fields` |
| `automation_scheduler/baseball_impact_readiness.py` | `` | `build_baseball_impact_readiness` |
| `automation_scheduler/baseball_impact_red_team.py` | `` | `evaluate_baseball_impact_red_team` |
| `automation_scheduler/baseball_impact_report.py` | `` | `_merge, _missing, _recommend, build_baseball_impact_diagnostics` |
| `automation_scheduler/baseball_incentive_context.py` | `` | `_threshold, evaluate_baseball_incentive_context` |
| `automation_scheduler/baseball_lineup_context.py` | `` | `evaluate_baseball_lineup_context` |
| `automation_scheduler/baseball_market_relevance.py` | `` | `_score, evaluate_baseball_market_relevance` |
| `automation_scheduler/baseball_matchup_context.py` | `` | `evaluate_baseball_matchup_context` |
| `automation_scheduler/baseball_park_weather_umpire_context.py` | `` | `_wind_modifier, _factor, evaluate_baseball_park_weather_umpire_context` |
| `automation_scheduler/baseball_pitcher_impact.py` | `` | `evaluate_baseball_pitcher_impact` |
| `automation_scheduler/baseball_run_value_impact.py` | `` | `_sample, evaluate_baseball_run_value_impact` |
| `automation_scheduler/basketball_incentive_context.py` | `` | `_threshold_pressure, evaluate_incentive_context` |
| `automation_scheduler/basketball_lineup_matchup_context.py` | `` | `_absence_shift, evaluate_lineup_matchup_context` |
| `automation_scheduler/basketball_market_relevance.py` | `` | `_score, _market_status, evaluate_market_relevance` |
| `automation_scheduler/basketball_player_impact.py` | `` | `_merge_candidate_inputs, _list_average, _injury_score, evaluate_availability_minutes, _downgrade_status, _recommend_status, run_basketball_player_impact` |
| `automation_scheduler/basketball_player_impact_calibration.py` | `` | `_market_family, _record_matches, _summarize, evaluate_basketball_player_impact_calibration` |
| `automation_scheduler/basketball_player_impact_common.py` | `` | `normalize_basketball_sport, sport_contract, safe_flags, _sensitive_key_for_basketball_output, redact_basketball_output, finalize_safe_response, safe_float, clamp, boolish, present_fields, missing_fields, weighted_average` |
| `automation_scheduler/basketball_player_impact_readiness.py` | `` | `build_basketball_player_impact_readiness` |
| `automation_scheduler/basketball_player_impact_red_team.py` | `` | `review_basketball_player_impact` |
| `automation_scheduler/basketball_possession_impact.py` | `` | `_rating_diff_score, _rate_edge_score, evaluate_possession_impact` |
| `automation_scheduler/basketball_role_context.py` | `` | `normalize_role, infer_player_role, evaluate_role_context` |
| `automation_scheduler/basketball_tracking_opportunity.py` | `` | `evaluate_tracking_opportunity` |
| `automation_scheduler/bayesian_structural_baseline.py` | `` | `_num, run_bayesian_structural_baseline` |
| `automation_scheduler/bookmaker_normalizer.py` | `` | `_slugify, normalize_bookmaker_name, normalize_entity_name, normalize_event_name, normalize_market_name, normalize_selection_name, normalize_odds_value, normalize_line_value, normalize_timestamp, normalize_offer` |
| `automation_scheduler/broker_quality_scoring.py` | `` | `_num, _clamp, score_broker_provider, default_broker_quality_rows, build_broker_quality_report` |
| `automation_scheduler/budget_gates.py` | `` | `default_approval_status, build_budget_gate` |
| `automation_scheduler/cadence_controller.py` | `` | `resolve_profile_name, choose_next_check_seconds` |
| `automation_scheduler/calibration.py` | `` | `_read_json, _report_dir, _atomic_write_json, _project_relative_path, _normalized_outcome_label, _bucket_probability, _bucket_score, _counter, _score_presence, _settlement_presence, _score_bucket_counts, _market_key` |
| `automation_scheduler/calibration_collector.py` | `` | `_env_bool, _env_int, collector_policy_from_env, _insufficient_sample, _collector_root, _watchlist_root, _atomic_write_json, _read_json, _project_relative, _parse_time, _iso, _market_key` |
| `automation_scheduler/calibration_tracker.py` | `` | `_to_float, _to_outcome, _bucket_label, bucket_predictions, calculate_brier_score, calculate_log_loss, summarize_calibration_by_bucket, calculate_expected_calibration_error, detect_overconfidence` |
| `automation_scheduler/candlestick_manifold_detector.py` | `` | `map_candlestick_context` |
| `automation_scheduler/candlestick_pattern_detector.py` | `` | `get_pattern_catalog, _num, _clamp, _candle, _volume_confirmation, _reward_risk, _build_pattern, detect_candlestick_patterns` |
| `automation_scheduler/causal_discovery_research.py` | `` | `run_causal_discovery_research` |
| `automation_scheduler/causal_scaffold.py` | `` | `_provided_confounder_count, evaluate_causal_hypothesis, build_causal_scaffold_report` |
| `automation_scheduler/clv_tracker.py` | `` | `_summary_float, _build_summary, summarize_clv_by_model, summarize_clv_by_market, build_clv_record, write_clv_record` |
| `automation_scheduler/collector_scheduled_runner.py` | `` | `_safe_response, validate_cron_token, _as_int, _validate_overrides, build_scheduled_collector_config, run_scheduled_collector_cycle` |
| `automation_scheduler/combat_availability_context.py` | `` | `evaluate_combat_availability_context` |
| `automation_scheduler/combat_damage_durability_context.py` | `` | `evaluate_combat_damage_durability_context, any_metric` |
| `automation_scheduler/combat_data_availability.py` | `` | `_merge, evaluate_combat_data_availability` |
| `automation_scheduler/combat_grappling_control_impact.py` | `` | `evaluate_combat_grappling_control_impact` |
| `automation_scheduler/combat_impact_calibration.py` | `` | `_count_outcomes, evaluate_combat_impact_calibration` |
| `automation_scheduler/combat_impact_common.py` | `` | `normalize_combat_sport, normalize_combat_market, safe_float, boolish, clamp, score_from_range, percent_score, categorical_score, weighted_average, compact_list, present_fields, missing_fields` |
| `automation_scheduler/combat_impact_readiness.py` | `` | `build_combat_impact_readiness` |
| `automation_scheduler/combat_impact_red_team.py` | `` | `evaluate_combat_impact_red_team` |

## Leakage Risk Scan
- Non-test files mentioning result/outcome/settlement/closing fields: `194`

| File | Line | Match |
|---|---:|---|
| `api_server.py` | 17 | `"/api/actions/betting/log-result",` |
| `asian_markets.py` | 91 | `If goal_diff_distribution provided (net goals vs line side), approximate win/push/half outcomes.` |
| `asian_markets.py` | 143 | `def mlb_market_grading_placeholder(market_type: str, result: str) -> dict[str, Any]:` |
| `asian_markets.py` | 147 | `"result": result,` |
| `asian_markets.py` | 157 | `def mlb_grade_full_game_moneyline(result: str) -> dict[str, Any]:` |
| `bet_decision_engine.py` | 131 | `return {"ok": False, "error": "INVALID_INPUT", "detail": "lines must be a non-empty list.", "results": []}` |
| `bet_decision_engine.py` | 134 | `return {"ok": False, "error": "INVALID_BANKROLL", "detail": "bankroll must be positive.", "results": []}` |
| `bet_decision_engine.py` | 137 | `return {"ok": False, "error": "INVALID_UNIT", "detail": "unit_size must be positive.", "results": []}` |
| `bet_decision_engine.py` | 157 | `return {"ok": False, "error": "INVALID_LINES", "detail": "No valid line objects.", "results": []}` |
| `bet_log.py` | 43 | `"result",` |
| `bet_log.py` | 115 | `def calculate_profit_loss(result: str \| None, stake: Any, odds_american: Any) -> float:` |
| `bet_log.py` | 116 | `normalized = (result or "").strip().lower()` |
| `bet_log.py` | 160 | `entry["result"] = entry.get("result") or "pending"` |
| `kalshi_client.py` | 23 | `result = {` |
| `kalshi_client.py` | 34 | `result.update({` |
| `kalshi_client.py` | 41 | `result.update({` |
| `kalshi_client.py` | 48 | `return result` |
| `main.py` | 35 | `from src.api.automation_review_outcomes_routes import register_automation_review_outcomes_routes` |
| `main.py` | 58 | `AutomationOutcomeIngestRequest,` |
| `main.py` | 59 | `AutomationOutcomeLocalSettlementImportRequest,` |
| `main.py` | 90 | `compact_outcome_ingest_response,` |
| `model_probability.py` | 75 | `class ModelProbabilityResult:` |
| `model_probability.py` | 76 | `"""Result of model probability calculation with transparency."""` |
| `model_probability.py` | 205 | `) -> ModelProbabilityResult:` |
| `model_probability.py` | 319 | `return ModelProbabilityResult(` |
| `multi_sport_model_registry.py` | 379 | `"backtesting dataset with settled outcomes",` |
| `multi_sport_model_registry.py` | 383 | `"settled outcomes by sport, market, and prop type",` |
| `multi_sport_model_registry.py` | 6220 | `["venue", "pitch condition", "toss result", "batting order", "bowling matchup", "run rate", "wicket rate", "weather"],` |
| `multi_sport_model_registry.py` | 10706 | `result = (team_goals - opponent_goals) + line` |
| `quant_engine.py` | 156 | `"result": "pending",` |
| `quant_engine.py` | 278 | `"""Total overround / vig for N outcomes: sum(implied) - 1."""` |
| `quant_engine.py` | 338 | `"backtest_requirements": ["settled outcomes", "closing-line history", "probability calibration buckets"],` |
| `risk_engine.py` | 222 | `"exposure_gate_result": "blocked" if blocked else "pass",` |
| `sharp_client.py` | 28 | `"result_type": "error",` |
| `sharp_client.py` | 77 | `"result_type": "odds" if has_actual_odds else "no_data",` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 57 | `("conformal_uncertainty", "Conformal Prediction", "blocked_insufficient_data", "needs_calibration_outcomes"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 58 | `("contrastive_embedding", "Contrastive Embedding Diagnostics", "research_only", "needs_labeled_outcomes"),` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 85 | `if _num(value) is not None and key.lower() not in {"final_outcome", "outcome", "label", "target"}` |
| `automation_scheduler/advanced_shape_diagnostics.py` | 94 | `if _num(value) is not None and key.lower() not in {"final_outcome", "outcome", "label", "target"}:` |
| `automation_scheduler/alert_engine.py` | 40 | `review_queue_gate_result = str(candidate.get("review_queue_gate_result") or "")` |
| `automation_scheduler/alert_engine.py` | 41 | `if governance_status == "blocked_by_governance" or review_queue_gate_result == "blocked_by_governance":` |
| `automation_scheduler/baseball_data_availability.py` | 43 | `"calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),` |
| `automation_scheduler/baseball_data_availability.py` | 116 | `calibration_allowed = "calibration_outcomes" in available` |
| `automation_scheduler/baseball_data_availability.py` | 128 | `cap_reasons.append("calibration_outcomes_missing")` |
| `automation_scheduler/baseball_data_availability.py` | 139 | `next_data.append("settled_outcomes_by_market_role_context")` |
| `automation_scheduler/baseball_impact_calibration.py` | 22 | `outcomes = _records(source.get("settled_outcomes"))` |
| `automation_scheduler/baseball_impact_calibration.py` | 23 | `explicit = int(safe_float(source.get("matched_outcomes_count"), 0.0) or 0)` |
| `automation_scheduler/baseball_impact_calibration.py` | 25 | `if predictions and outcomes:` |
| `automation_scheduler/baseball_impact_calibration.py` | 26 | `outcome_ids = {str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")) for item in outcomes}` |
| `automation_scheduler/baseball_impact_readiness.py` | 35 | `"real_settled_outcomes_required",` |
| `automation_scheduler/baseball_impact_red_team.py` | 104 | `missing.extend(cal.get("next_required_data") or ["settled_outcomes"])` |
| `automation_scheduler/basketball_player_impact.py` | 194 | `outcome_records: list[dict[str, Any]] \| None = None,` |
| `automation_scheduler/basketball_player_impact.py` | 219 | `calibration = evaluate_basketball_player_impact_calibration(source, outcome_records or [], market_type=source.get("market_type") or source.get("market"))` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 73 | `outcome = str(record.get("outcome") or record.get("result") or "").strip().lower()` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 76 | `hit = outcome in {"hit", "win", "won", "success", "covered", "over_hit", "under_hit"}` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 79 | `elif outcome or record.get("hit") is not None:` |
| `automation_scheduler/basketball_player_impact_calibration.py` | 110 | `"outcome_coverage": round(clamp(sample / max(required_sample_size, 1) * 100.0) / 100.0, 4),` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 60 | `"minutes_outcomes",` |
| `automation_scheduler/basketball_player_impact_readiness.py` | 61 | `"settled_market_outcomes",` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 10 | `player_impact_result: dict[str, Any] \| None = None,` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 15 | `result = player_impact_result if isinstance(player_impact_result, dict) else {}` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 24 | `possession_status = str(result.get("possession_impact", {}).get("possession_impact_status") or result.get("possession_impact_status") or "").lower()` |
| `automation_scheduler/basketball_player_impact_red_team.py` | 25 | `tracking_status = str(result.get("tracking_opportunity", {}).get("tracking_status") or result.get("tracking_status") or "").lower()` |
| `automation_scheduler/bayesian_structural_baseline.py` | 30 | `value = _num(row.get("outcome_value") or row.get("actual") or row.get("return") or row.get("delta"))` |
| `automation_scheduler/bayesian_structural_baseline.py` | 54 | `observed = _num(candidate.get("observed_outcome") or candidate.get("observed_value") or candidate.get("edge_estimate")) or mean` |
| `automation_scheduler/calibration.py` | 8 | `from .outcome_store import load_outcome_records, load_outcome_state, summarize_outcomes` |
| `automation_scheduler/calibration.py` | 13 | `CALIBRATION_SCHEMA_VERSION = f"{SCHEMA_VERSION}.outcome_calibration.v1"` |
| `automation_scheduler/calibration.py` | 14 | `_OUTCOME_KEYS = ("outcome_status", "settlement_status", "final_outcome", "paper_result", "settled_at")` |
| `automation_scheduler/calibration.py` | 55 | `def _normalized_outcome_label(value: Any) -> float \| None:` |
| `automation_scheduler/calibration_collector.py` | 17 | `from .outcome_store import ingest_outcome_records, load_outcome_records` |
| `automation_scheduler/calibration_collector.py` | 29 | `SETTLED_CLASSIFICATIONS = {"settled_yes", "settled_no", "void_or_cancelled"}` |
| `automation_scheduler/calibration_collector.py` | 83 | `"min_target_outcomes": _env_int("KALSHI_CALIBRATION_MIN_TARGET_OUTCOMES", 30),` |
| `automation_scheduler/calibration_collector.py` | 84 | `"good_target_outcomes": _env_int("KALSHI_CALIBRATION_GOOD_TARGET_OUTCOMES", 100),` |
| `automation_scheduler/calibration_tracker.py` | 24 | `def _to_outcome(value: Any) -> float \| None:` |
| `automation_scheduler/calibration_tracker.py` | 44 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/calibration_tracker.py` | 58 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/calibration_tracker.py` | 72 | `y = _to_outcome(row.get("result_status"))` |
| `automation_scheduler/candlestick_manifold_detector.py` | 18 | `result = map_market_state(` |
| `automation_scheduler/candlestick_manifold_detector.py` | 25 | `pattern_quality = result.get("normalized_feature_summary", {}).get("pattern_quality_score")` |
| `automation_scheduler/candlestick_manifold_detector.py` | 28 | `reliability = float(result.get("cluster_reliability_score") or 0.0)` |
| `automation_scheduler/candlestick_manifold_detector.py` | 29 | `trap = max(float(result.get("no_trade_trap_score") or 0.0), float(result.get("no_bet_trap_score") or 0.0))` |
| `automation_scheduler/causal_scaffold.py` | 14 | `"outcome_variable": "player_usage_or_prop_line_move",` |
| `automation_scheduler/causal_scaffold.py` | 20 | `"outcome_variable": "total_or_points_prop_hit_rate",` |
| `automation_scheduler/causal_scaffold.py` | 26 | `"outcome_variable": "fake_edge_or_negative_ev_rate",` |
| `automation_scheduler/causal_scaffold.py` | 32 | `"outcome_variable": "momentum_follow_through",` |
| `automation_scheduler/collector_scheduled_runner.py` | 15 | `"persist_outcomes": True,` |
| `automation_scheduler/collector_scheduled_runner.py` | 44 | `"infer_outcomes",` |
| `automation_scheduler/collector_scheduled_runner.py` | 45 | `"inferred_outcomes",` |
| `automation_scheduler/collector_scheduled_runner.py` | 46 | `"allow_inferred_outcomes",` |
| `automation_scheduler/combat_data_availability.py` | 37 | `"calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),` |
| `automation_scheduler/combat_data_availability.py` | 132 | `calibration_allowed = "calibration_outcomes" in available` |
| `automation_scheduler/combat_data_availability.py` | 149 | `next_data.append("settled_combat_market_outcomes")` |
| `automation_scheduler/combat_impact_calibration.py` | 11 | `def _count_outcomes(payload: dict[str, Any]) -> int:` |
| `automation_scheduler/combat_impact_calibration.py` | 12 | `outcomes = payload.get("settled_outcomes")` |
| `automation_scheduler/combat_impact_calibration.py` | 13 | `if isinstance(outcomes, list):` |
| `automation_scheduler/combat_impact_calibration.py` | 14 | `return len(outcomes)` |
| `automation_scheduler/combat_impact_readiness.py` | 39 | `"moneyline": ["fighter_identity", "summary_striking_grappling", "settled_moneyline_outcomes"],` |
| `automation_scheduler/combat_impact_readiness.py` | 40 | `"method_markets": ["finish_path_outcomes", "durability_context", "submission_control_context"],` |
| `automation_scheduler/combat_impact_readiness.py` | 41 | `"round_total_markets": ["round_level_pace_damage", "cardio_decline_context", "finish_timing_outcomes"],` |
| `automation_scheduler/combat_impact_readiness.py` | 43 | `"boxing_props": ["jab_power_punch_tracking", "round_projection", "settled_boxing_prop_outcomes"],` |
| `automation_scheduler/combat_impact_red_team.py` | 96 | `missing.extend(calib.get("next_required_data") or ["settled_combat_market_outcomes"])` |
| `automation_scheduler/combat_phase_control_context.py` | 60 | `if source.get("final_result") and not phase_scores:` |
| `automation_scheduler/combat_phase_control_context.py` | 61 | `no_bet.append("phase_control_not_inferred_from_final_result")` |
| `automation_scheduler/conformal_uncertainty.py` | 21 | `actual = _num(row.get("actual") or row.get("realized_edge") or row.get("outcome"))` |
| `automation_scheduler/conformal_uncertainty.py` | 34 | `minimum_outcomes: int = 50,` |
| `automation_scheduler/conformal_uncertainty.py` | 38 | `if len(residuals) < int(minimum_outcomes):` |
| `automation_scheduler/conformal_uncertainty.py` | 49 | `"conformal_no_bet_reason": "insufficient_calibration_outcomes",` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 8 | `def _outcome_label(row: Mapping[str, Any]) -> str \| None:` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 9 | `value = str(row.get("final_outcome") or row.get("outcome") or row.get("label") or row.get("paper_result") or "").strip().lower()` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 72 | `rows = [row for row in (labeled_records or []) if isinstance(row, Mapping) and _outcome_label(row)]` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | 93 | `paired.append((_outcome_label(row), vector_similarity(candidate_vector, vec)))` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 30 | `total_labeled_outcomes: int = 0,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 31 | `outcome_coverage_by_asset_type: dict[str, Any] \| None = None,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 44 | `total_labeled_outcomes=total_labeled_outcomes,` |
| `automation_scheduler/cross_asset_intelligence_router.py` | 45 | `outcome_coverage_by_asset_type=outcome_coverage_by_asset_type,` |
| `automation_scheduler/data_availability_tiers.py` | 18 | `0: "TIER_0_OUTCOME_BACKFILL",` |
| `automation_scheduler/data_availability_tiers.py` | 26 | `0: ["schedule", "teams", "event_date", "home_away", "final_score", "final_result", "margin", "total"],` |
| `automation_scheduler/data_availability_tiers.py` | 37 | `0: "outcome_backfill_and_tier_0_calibration_only",` |
| `automation_scheduler/data_availability_tiers.py` | 45 | `-1: "no-call audit for schedule/results/outcome fields",` |
| `automation_scheduler/data_intelligence_registry.py` | 33 | `"calibration_outcome_tracking",` |
| `automation_scheduler/data_intelligence_registry.py` | 74 | `total_labeled_outcomes: int = 0,` |
| `automation_scheduler/data_intelligence_registry.py` | 75 | `outcome_coverage_by_asset_type: Mapping[str, Any] \| None = None,` |
| `automation_scheduler/data_intelligence_registry.py` | 78 | `total_labeled_outcomes=total_labeled_outcomes,` |
| `automation_scheduler/data_paths.py` | 81 | `def get_outcomes_dir() -> Path:` |
| `automation_scheduler/data_paths.py` | 82 | `return get_runtime_data_path("outcomes")` |
| `automation_scheduler/data_source_registry.py` | 184 | `"final_results",` |
| `automation_scheduler/data_source_registry.py` | 195 | `"final_results",` |
| `automation_scheduler/data_source_registry.py` | 212 | `"settlement_result",` |
| `automation_scheduler/data_source_registry.py` | 346 | `"final_results": False,` |
| `automation_scheduler/data_source_research_lanes.py` | 18 | `"Map final outcome fields",` |
| `automation_scheduler/data_source_research_lanes.py` | 29 | `"outcome mapping completed",` |
| `automation_scheduler/data_source_research_lanes.py` | 70 | `"outcome_fields_required": list(lane.get("outcome_fields_required") or []),` |
| `automation_scheduler/deepseek_data_pull_check.py` | 13 | `from .prediction_market_outcome_candidates import build_candidate_report` |
| `automation_scheduler/deepseek_data_pull_check.py` | 176 | `"explicit_outcomes_found": 0,` |
| `automation_scheduler/deepseek_data_pull_check.py` | 189 | `"prediction_market_outcome_check_enabled": False,` |
| `automation_scheduler/deepseek_data_pull_check.py` | 202 | `"prediction_market_outcome_check_enabled": True,` |
| `automation_scheduler/deepseek_profit_lab.py` | 30 | `from .outcome_store import load_outcome_state, summarize_outcomes` |
| `automation_scheduler/deepseek_profit_lab.py` | 138 | `outcome_summary: Mapping[str, Any] \| None = None,` |
| `automation_scheduler/deepseek_profit_lab.py` | 159 | `"outcome_summary": dict(outcome_summary or {}),` |
| `automation_scheduler/deepseek_profit_lab.py` | 194 | `outcomes = load_outcome_state(base)` |
| `automation_scheduler/deepseek_prompt_contracts.py` | 16 | `Do not fabricate outcomes, probabilities, settlement results, historical performance, or calibration support.` |
| `automation_scheduler/deepseek_prompt_contracts.py` | 102 | `"Task: produce a compact daily Profit Lab red-team report from the supplied summaries. Focus on where edge is real, fake, unsupported, stale, trapped by liquidity/spread/settlement, or contradicted by outcomes/calibratio` |
| `automation_scheduler/deepseek_response_validator.py` | 244 | `"next_data_to_collect": ["compact_redacted_calibration_and_outcome_evidence"],` |
| `automation_scheduler/deepseek_response_validator.py` | 327 | `"recommended_next_data_to_collect": ["compact_outcome_and_calibration_evidence"],` |
| `automation_scheduler/deepseek_reviewer.py` | 14 | `"persist_outcome",` |
| `automation_scheduler/deepseek_reviewer.py` | 123 | `"outcome_status": row.get("outcome_status"),` |
| `automation_scheduler/deepseek_reviewer.py` | 124 | `"final_outcome": row.get("final_outcome"),` |
| `automation_scheduler/deepseek_reviewer.py` | 189 | `if row.get("final_outcome") and row.get("outcome_status") not in {"settled", "void", "cancelled"}:` |
| `automation_scheduler/deep_learning_research_lanes.py` | 29 | `"data_required": "broad unlabeled feature snapshots plus labeled holdout outcomes",` |
| `automation_scheduler/deep_learning_research_lanes.py` | 37 | `"data_required": "large cross-asset feature and outcome history",` |
| `automation_scheduler/deep_learning_research_lanes.py` | 45 | `"data_required": "validated event-entity graph with labeled outcomes",` |
| `automation_scheduler/deep_learning_research_lanes.py` | 53 | `"data_required": "relationship graph snapshots with outcome labels",` |
| `automation_scheduler/derived_feature_backfill_report.py` | 106 | `"result",` |
| `automation_scheduler/derived_feature_backfill_report.py` | 108 | `"prediction_market_outcome",` |
| `automation_scheduler/derived_feature_backfill_report.py` | 127 | `"missing_scores_or_results",` |
| `automation_scheduler/derived_feature_backfill_report.py` | 129 | `"missing_explicit_outcomes",` |
| `automation_scheduler/derived_feature_planner.py` | 13 | `"rolling_win_rate": {"fields": ["result"], "history": 3},` |
| `automation_scheduler/derived_feature_planner.py` | 14 | `"home_away_split": {"fields": ["home_away", "result"], "history": 3},` |
| `automation_scheduler/derived_feature_planner.py` | 21 | `"prediction_market_outcome": {"fields": ["settlement_result"], "history": 1},` |
| `automation_scheduler/derived_feature_planner.py` | 33 | `"final_score": {"final_score", "points_for", "points_against", "result"},` |
| `automation_scheduler/drawdown_controls.py` | 10 | `gate_result = "pass"` |
| `automation_scheduler/drawdown_controls.py` | 14 | `gate_result = "blocked"` |
| `automation_scheduler/drawdown_controls.py` | 17 | `gate_result = "reduced_half"` |
| `automation_scheduler/drawdown_controls.py` | 20 | `gate_result = "reduced_quarter"` |
| `automation_scheduler/ev_line_shopper.py` | 60 | `result = shop_ev_lines(offers, model_probability=model_probability, stake=stake)` |
| `automation_scheduler/ev_line_shopper.py` | 61 | `best = result.get("best_line_available")` |
| `automation_scheduler/ev_line_shopper.py` | 65 | `return result` |
| `automation_scheduler/ev_line_shopper.py` | 73 | `result = shop_ev_lines(offers, model_probability=model_probability, stake=stake)` |
| `automation_scheduler/execution_authorization.py` | 71 | `result = {` |
| `automation_scheduler/execution_authorization.py` | 94 | `denial_reason=";".join(result["execution_blockers"]),` |
| `automation_scheduler/execution_authorization.py` | 99 | `response_payload=result,` |
| `automation_scheduler/execution_authorization.py` | 102 | `return result` |
| `automation_scheduler/execution_gatekeeper.py` | 21 | `hard_gate_result: Mapping[str, Any] \| None = None,` |
| `automation_scheduler/execution_gatekeeper.py` | 37 | `hard = dict(hard_gate_result or evaluate_hard_gates(safe_candidate, persist_audit=False))` |
| `automation_scheduler/extreme_signal_red_team.py` | 15 | `result = diagnose_extreme_randomness(candidate, baseline_values=baseline_values, matrix_payload=matrix_payload)` |
| `automation_scheduler/extreme_signal_red_team.py` | 16 | `item = dict(result.get("sample_item") or {})` |
| `automation_scheduler/extreme_signal_red_team.py` | 24 | `"diagnostics": result,` |
| `automation_scheduler/football_data_availability.py` | 106 | `"calibration_outcomes": (` |
| `automation_scheduler/football_data_availability.py` | 108 | `"settled_outcomes",` |
| `automation_scheduler/football_data_availability.py` | 109 | `"matched_outcomes_count",` |
| `automation_scheduler/football_data_availability.py` | 110 | `"final_outcome",` |
| `automation_scheduler/football_impact_calibration.py` | 14 | `def _matched_records(predictions: list[dict[str, Any]], outcomes: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:` |
| `automation_scheduler/football_impact_calibration.py` | 16 | `for outcome in outcomes:` |
| `automation_scheduler/football_impact_calibration.py` | 17 | `key = outcome.get("prediction_id") or outcome.get("candidate_id") or outcome.get("event_id") or outcome.get("id")` |
| `automation_scheduler/football_impact_calibration.py` | 19 | `by_id[str(key)] = outcome` |
| `automation_scheduler/football_impact_red_team.py` | 75 | `missing.extend(calibration.get("next_required_data") or ["settled_outcomes"])` |
| `automation_scheduler/football_impact_report.py` | 201 | `result = {` |
| `automation_scheduler/football_impact_report.py` | 233 | `return finalize_football_response(result, source_payload=source_payload)` |
| `automation_scheduler/football_impact_report.py` | 240 | `"settled_outcome_calibration_buckets",` |
| `automation_scheduler/football_impact_report.py` | 267 | `"americanfootball_nfl": ["settled_outcome_calibration_buckets", "optional_tracking_context"],` |
| `automation_scheduler/football_play_drive_impact.py` | 133 | `result = {` |
| `automation_scheduler/football_play_drive_impact.py` | 156 | `result["status"] = "missing"` |
| `automation_scheduler/football_play_drive_impact.py` | 158 | `result["status"] = "limited"` |
| `automation_scheduler/football_play_drive_impact.py` | 160 | `result["status"] = "ready"` |
| `automation_scheduler/football_role_impact.py` | 371 | `result = {` |
| `automation_scheduler/football_role_impact.py` | 386 | `return finalize_football_response(result, source_payload=source)` |

## Readiness Assessment

### What looks ready
- You have ledger / CLV / outcome-related code or artifacts.
- You have bankroll / staking / risk sizing logic.
- You have backtest / historical / simulation-related code.
- You have model training / regression / calibration-related code.
- You have feature engineering / signal-related code.

### Likely gaps to verify/fix

## Practical Verdict
READY_LEVEL: `paper_to_backtest_foundation_exists`

The repo appears to have enough foundation to begin a controlled backtesting readiness phase, but we still need to verify data quality, no lookahead leakage, bankroll accounting, and repeatable historical replay.

## Next Recommended Phase

Phase 10A should build or verify a single canonical historical dataset with:
- event_id / contract_id
- sport / league / market
- open time and close time
- odds / prices available before decision time
- model features available before decision time
- decision timestamp
- stake / unit size
- final outcome
- payout / pnl
- closing line / CLV fields
