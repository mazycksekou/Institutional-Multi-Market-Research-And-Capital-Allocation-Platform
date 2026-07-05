from __future__ import annotations

from typing import Any, Optional

from fastapi import Body, Depends, HTTPException, Query, Request

from src.api.schemas.automation import (
    AutomationAdvancedShapeDiagnosticsRequest,
    AutomationBaseballImpactDiagnosticsRequest,
    AutomationBasketballPlayerImpactRequest,
    AutomationCombatImpactDiagnosticsRequest,
    AutomationExtremeSignalDiagnosticsRequest,
    AutomationFootballImpactDiagnosticsRequest,
    AutomationGolfImpactDiagnosticsRequest,
    AutomationHockeyImpactDiagnosticsRequest,
    AutomationSoccerImpactDiagnosticsRequest,
    AutomationTennisImpactDiagnosticsRequest,
)

def register_automation_sport_impact_routes(
    app: Any,
    *,
    dashboard_facade_dep: Any,
    compact_advanced_red_team_response_dep: Any,
    compact_baseball_impact_diagnostics_response_dep: Any,
    compact_baseball_impact_readiness_response_dep: Any,
    compact_basketball_player_impact_readiness_response_dep: Any,
    compact_basketball_player_impact_response_dep: Any,
    compact_combat_impact_diagnostics_response_dep: Any,
    compact_combat_impact_readiness_response_dep: Any,
    compact_extreme_randomness_diagnostics_response_dep: Any,
    compact_extreme_randomness_report_response_dep: Any,
    compact_football_impact_diagnostics_response_dep: Any,
    compact_football_impact_readiness_response_dep: Any,
    compact_golf_impact_diagnostics_response_dep: Any,
    compact_golf_impact_readiness_response_dep: Any,
    compact_hockey_impact_diagnostics_response_dep: Any,
    compact_hockey_impact_readiness_response_dep: Any,
    compact_soccer_impact_diagnostics_response_dep: Any,
    compact_soccer_impact_readiness_response_dep: Any,
    compact_tennis_impact_diagnostics_response_dep: Any,
    compact_tennis_impact_readiness_response_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register automation sport impact/readiness/diagnostics routes.

    Canonical owner: src/api/automation_sport_impact_routes.py
    """
    dashboard_facade = dashboard_facade_dep
    compact_advanced_red_team_response = compact_advanced_red_team_response_dep
    compact_baseball_impact_diagnostics_response = compact_baseball_impact_diagnostics_response_dep
    compact_baseball_impact_readiness_response = compact_baseball_impact_readiness_response_dep
    compact_basketball_player_impact_readiness_response = compact_basketball_player_impact_readiness_response_dep
    compact_basketball_player_impact_response = compact_basketball_player_impact_response_dep
    compact_combat_impact_diagnostics_response = compact_combat_impact_diagnostics_response_dep
    compact_combat_impact_readiness_response = compact_combat_impact_readiness_response_dep
    compact_extreme_randomness_diagnostics_response = compact_extreme_randomness_diagnostics_response_dep
    compact_extreme_randomness_report_response = compact_extreme_randomness_report_response_dep
    compact_football_impact_diagnostics_response = compact_football_impact_diagnostics_response_dep
    compact_football_impact_readiness_response = compact_football_impact_readiness_response_dep
    compact_golf_impact_diagnostics_response = compact_golf_impact_diagnostics_response_dep
    compact_golf_impact_readiness_response = compact_golf_impact_readiness_response_dep
    compact_hockey_impact_diagnostics_response = compact_hockey_impact_diagnostics_response_dep
    compact_hockey_impact_readiness_response = compact_hockey_impact_readiness_response_dep
    compact_soccer_impact_diagnostics_response = compact_soccer_impact_diagnostics_response_dep
    compact_soccer_impact_readiness_response = compact_soccer_impact_readiness_response_dep
    compact_tennis_impact_diagnostics_response = compact_tennis_impact_diagnostics_response_dep
    compact_tennis_impact_readiness_response = compact_tennis_impact_readiness_response_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.get("/api/automation/basketball-player-impact-readiness", operation_id="getAutomationBasketballPlayerImpactReadiness")
    async def get_automation_basketball_player_impact_readiness_endpoint(
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=20),
    ):
        cap = min(max(int(limit), 1), 100 if verbose else 20)
        payload = dashboard_facade.get_basketball_player_impact_readiness()
        compact = compact_basketball_player_impact_readiness_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/basketball-player-impact", operation_id="runAutomationBasketballPlayerImpact")
    async def automation_basketball_player_impact_endpoint(
        payload: AutomationBasketballPlayerImpactRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=20),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="basketball player-impact analysis only supports dry_run=true")
        cap = min(max(int(limit), 1), 100 if verbose else 20)
        result = dashboard_facade.run_automation_basketball_player_impact(
            candidate=payload.candidate,
            outcome_records=payload.outcome_records,
            red_team_provider=payload.red_team_provider,
        )
        compact = compact_basketball_player_impact_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/advanced-red-team-report", operation_id="getAutomationAdvancedRedTeamReport")
    async def get_automation_advanced_red_team_report_endpoint(
        provider: Optional[str] = Query(default=None),
        persist_report: bool = Query(default=False),
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        payload = dashboard_facade.get_automation_advanced_red_team_report(
            provider=provider,
            persist_report=persist_report,
            max_items=cap,
        )
        compact = compact_advanced_red_team_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/extreme-randomness-report", operation_id="getAutomationExtremeRandomnessReport")
    async def get_automation_extreme_randomness_report_endpoint(
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        payload = dashboard_facade.get_extreme_randomness_report()
        compact = compact_extreme_randomness_report_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/football-impact-readiness", operation_id="getAutomationFootballImpactReadiness")
    async def get_automation_football_impact_readiness_endpoint(
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        payload = dashboard_facade.get_football_impact_readiness()
        compact = compact_football_impact_readiness_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/football-impact-diagnostics", operation_id="runAutomationFootballImpactDiagnostics")
    async def automation_football_impact_diagnostics_endpoint(
        payload: AutomationFootballImpactDiagnosticsRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="football impact diagnostics only supports dry_run=true")
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        result = dashboard_facade.run_football_impact_diagnostics(
            sport=payload.sport,
            market_type=payload.market_type,
            team_context=payload.team_context,
            player_context=payload.player_context,
            play_drive_context=payload.play_drive_context,
            personnel_context=payload.personnel_context,
            matchup_context=payload.matchup_context,
            availability_context=payload.availability_context,
            incentive_context=payload.incentive_context,
            calibration_context=payload.calibration_context,
            tracking_context=payload.tracking_context,
            dry_run=True,
        )
        compact = compact_football_impact_diagnostics_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/soccer-impact-readiness", operation_id="getAutomationSoccerImpactReadiness")
    async def get_automation_soccer_impact_readiness_endpoint(
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        payload = dashboard_facade.get_soccer_impact_readiness()
        compact = compact_soccer_impact_readiness_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/soccer-impact-diagnostics", operation_id="runAutomationSoccerImpactDiagnostics")
    async def automation_soccer_impact_diagnostics_endpoint(
        payload: AutomationSoccerImpactDiagnosticsRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="soccer impact diagnostics only supports dry_run=true")
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        result = dashboard_facade.run_soccer_impact_diagnostics(
            sport=payload.sport,
            market_type=payload.market_type,
            game_context=payload.game_context,
            team_context=payload.team_context,
            player_context=payload.player_context,
            lineup_context=payload.lineup_context,
            tactical_context=payload.tactical_context,
            possession_value_context=payload.possession_value_context,
            shot_quality_context=payload.shot_quality_context,
            pressing_context=payload.pressing_context,
            transition_context=payload.transition_context,
            set_piece_context=payload.set_piece_context,
            goalkeeper_context=payload.goalkeeper_context,
            referee_context=payload.referee_context,
            matchup_context=payload.matchup_context,
            availability_context=payload.availability_context,
            incentive_context=payload.incentive_context,
            calibration_context=payload.calibration_context,
            tracking_context=payload.tracking_context,
            dry_run=True,
        )
        compact = compact_soccer_impact_diagnostics_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/hockey-impact-readiness", operation_id="getAutomationHockeyImpactReadiness")
    async def get_automation_hockey_impact_readiness_endpoint(
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        payload = dashboard_facade.get_hockey_impact_readiness()
        compact = compact_hockey_impact_readiness_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/hockey-impact-diagnostics", operation_id="runAutomationHockeyImpactDiagnostics")
    async def automation_hockey_impact_diagnostics_endpoint(
        payload: AutomationHockeyImpactDiagnosticsRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="hockey impact diagnostics only supports dry_run=true")
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        result = dashboard_facade.run_hockey_impact_diagnostics(
            sport=payload.sport,
            market_type=payload.market_type,
            game_context=payload.game_context,
            team_context=payload.team_context,
            skater_context=payload.skater_context,
            goalie_context=payload.goalie_context,
            line_context=payload.line_context,
            pair_context=payload.pair_context,
            special_teams_context=payload.special_teams_context,
            transition_context=payload.transition_context,
            shot_quality_context=payload.shot_quality_context,
            matchup_context=payload.matchup_context,
            availability_context=payload.availability_context,
            incentive_context=payload.incentive_context,
            calibration_context=payload.calibration_context,
            tracking_context=payload.tracking_context,
            dry_run=True,
        )
        compact = compact_hockey_impact_diagnostics_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/baseball-impact-readiness", operation_id="getAutomationBaseballImpactReadiness")
    async def get_automation_baseball_impact_readiness_endpoint(
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=50),
    ):
        cap = min(max(int(limit), 1), 100 if verbose else 50)
        payload = dashboard_facade.get_baseball_impact_readiness()
        compact = compact_baseball_impact_readiness_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/baseball-impact-diagnostics", operation_id="runAutomationBaseballImpactDiagnostics")
    async def automation_baseball_impact_diagnostics_endpoint(
        payload: AutomationBaseballImpactDiagnosticsRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="baseball impact diagnostics only supports dry_run=true")
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        result = dashboard_facade.run_baseball_impact_diagnostics(
            sport=payload.sport,
            market_type=payload.market_type,
            game_context=payload.game_context,
            team_context=payload.team_context,
            pitcher_context=payload.pitcher_context,
            batter_context=payload.batter_context,
            lineup_context=payload.lineup_context,
            bullpen_context=payload.bullpen_context,
            catcher_context=payload.catcher_context,
            defense_context=payload.defense_context,
            baserunning_context=payload.baserunning_context,
            park_weather_context=payload.park_weather_context,
            umpire_context=payload.umpire_context,
            availability_context=payload.availability_context,
            incentive_context=payload.incentive_context,
            calibration_context=payload.calibration_context,
            tracking_context=payload.tracking_context,
            dry_run=True,
        )
        compact = compact_baseball_impact_diagnostics_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/golf-impact-readiness", operation_id="getAutomationGolfImpactReadiness")
    async def get_automation_golf_impact_readiness_endpoint(
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=50),
    ):
        cap = min(max(int(limit), 1), 100 if verbose else 50)
        payload = dashboard_facade.get_golf_impact_readiness()
        compact = compact_golf_impact_readiness_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/golf-impact-diagnostics", operation_id="runAutomationGolfImpactDiagnostics")
    async def automation_golf_impact_diagnostics_endpoint(
        payload: AutomationGolfImpactDiagnosticsRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="golf impact diagnostics only supports dry_run=true")
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        result = dashboard_facade.run_golf_impact_diagnostics(
            sport=payload.sport,
            market_type=payload.market_type,
            tournament_context=payload.tournament_context,
            player_context=payload.player_context,
            strokes_gained_context=payload.strokes_gained_context,
            off_tee_context=payload.off_tee_context,
            approach_context=payload.approach_context,
            around_green_context=payload.around_green_context,
            putting_context=payload.putting_context,
            course_context=payload.course_context,
            weather_context=payload.weather_context,
            wave_context=payload.wave_context,
            field_context=payload.field_context,
            form_context=payload.form_context,
            availability_context=payload.availability_context,
            incentive_context=payload.incentive_context,
            calibration_context=payload.calibration_context,
            simulation_context=payload.simulation_context,
            tracking_context=payload.tracking_context,
            dry_run=True,
        )
        compact = compact_golf_impact_diagnostics_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/combat-impact-readiness", operation_id="getAutomationCombatImpactReadiness")
    async def get_automation_combat_impact_readiness_endpoint(
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=50),
    ):
        cap = min(max(int(limit), 1), 100 if verbose else 50)
        payload = dashboard_facade.get_combat_impact_readiness()
        compact = compact_combat_impact_readiness_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/combat-impact-diagnostics", operation_id="runAutomationCombatImpactDiagnostics")
    async def automation_combat_impact_diagnostics_endpoint(
        payload: AutomationCombatImpactDiagnosticsRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="combat impact diagnostics only supports dry_run=true")
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        result = dashboard_facade.run_combat_impact_diagnostics(
            sport=payload.sport,
            market_type=payload.market_type,
            bout_context=payload.bout_context,
            fighter_a_context=payload.fighter_a_context,
            fighter_b_context=payload.fighter_b_context,
            striking_context=payload.striking_context,
            grappling_context=payload.grappling_context,
            phase_context=payload.phase_context,
            damage_context=payload.damage_context,
            pace_cardio_context=payload.pace_cardio_context,
            matchup_context=payload.matchup_context,
            ruleset_context=payload.ruleset_context,
            judging_referee_context=payload.judging_referee_context,
            availability_context=payload.availability_context,
            incentive_context=payload.incentive_context,
            calibration_context=payload.calibration_context,
            film_tracking_context=payload.film_tracking_context,
            dry_run=True,
        )
        compact = compact_combat_impact_diagnostics_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/tennis-impact-readiness", operation_id="getAutomationTennisImpactReadiness")
    async def get_automation_tennis_impact_readiness_endpoint(
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=50),
    ):
        cap = min(max(int(limit), 1), 100 if verbose else 50)
        payload = dashboard_facade.get_tennis_impact_readiness()
        compact = compact_tennis_impact_readiness_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/tennis-impact-diagnostics", operation_id="runAutomationTennisImpactDiagnostics")
    async def automation_tennis_impact_diagnostics_endpoint(
        payload: AutomationTennisImpactDiagnosticsRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="tennis impact diagnostics only supports dry_run=true")
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        result = dashboard_facade.run_tennis_impact_diagnostics(
            sport=payload.sport,
            market_type=payload.market_type,
            match_context=payload.match_context,
            player_a_context=payload.player_a_context,
            player_b_context=payload.player_b_context,
            serve_context=payload.serve_context,
            return_context=payload.return_context,
            surface_context=payload.surface_context,
            format_context=payload.format_context,
            pressure_context=payload.pressure_context,
            tiebreak_context=payload.tiebreak_context,
            matchup_context=payload.matchup_context,
            conditions_context=payload.conditions_context,
            availability_context=payload.availability_context,
            incentive_context=payload.incentive_context,
            calibration_context=payload.calibration_context,
            point_context=payload.point_context,
            tracking_context=payload.tracking_context,
            dry_run=True,
        )
        compact = compact_tennis_impact_diagnostics_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/extreme-signal-diagnostics", operation_id="runAutomationExtremeSignalDiagnostics")
    async def automation_extreme_signal_diagnostics_endpoint(
        payload: AutomationExtremeSignalDiagnosticsRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="extreme signal diagnostics only supports dry_run=true")
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        result = dashboard_facade.run_extreme_randomness_diagnostics(
            candidate=payload.candidate,
            baseline_values=payload.baseline_values or None,
            matrix_payload=payload.matrix_payload or None,
        )
        compact = compact_extreme_randomness_diagnostics_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/advanced-shape-diagnostics", operation_id="runAutomationAdvancedShapeDiagnostics")
    async def automation_advanced_shape_diagnostics_endpoint(
        payload: AutomationAdvancedShapeDiagnosticsRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="advanced shape diagnostics only supports dry_run=true")
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        result = dashboard_facade.run_automation_advanced_shape_diagnostics(
            candidate=payload.candidate,
            historical_records=payload.historical_records,
            labeled_records=payload.labeled_records,
            calibration_records=payload.calibration_records,
            sequences=payload.sequences,
            provider=payload.provider,
            persist=payload.persist,
        )
        compact = compact_advanced_red_team_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact

