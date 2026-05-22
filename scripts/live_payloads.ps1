$ErrorActionPreference = "Stop"

function New-LiveTicketBase {
    param(
        [Parameter(Mandatory = $true)] [string] $Sport,
        [string] $League,
        [string] $Event = "Live Smoke Event",
        [string] $Market = "moneyline",
        [string] $Selection = "Smoke Selection",
        [int] $OddsAmerican = 100,
        $InputStats = @{}
    )
    return @{
        source_type = "chatgpt_parsed"
        sport = $Sport
        league = $League
        event = $Event
        market = $Market
        selection = $Selection
        odds_american = $OddsAmerican
        bankroll = 1000
        unit_size = 25
        risk_profile = "moderate"
        screenshot_text = "$Selection $Market +100"
        input_stats = $InputStats
    }
}

function New-LiveMissingPayload {
    param([Parameter(Mandatory = $true)] [string] $Sport)
    return New-LiveTicketBase -Sport $Sport -League $Sport.ToUpper() -InputStats @{}
}

function New-LiveBadTextPayload {
    param([Parameter(Mandatory = $true)] [string] $Sport)
    return New-LiveTicketBase -Sport $Sport -League $Sport.ToUpper() -InputStats "bad text input"
}

function New-NbaPayload {
    $stats = @{
        team_name = "Celtics"; opponent_name = "Knicks"; selection_name = "Celtics"; matchup = "Knicks at Celtics"; home_away = "home"
        team_pace = 101.5; opponent_pace = 98.2; team_offensive_rating = 121.0; opponent_offensive_rating = 113.0
        team_defensive_rating = 110.0; opponent_defensive_rating = 116.0; team_efg_percent = 0.575; opponent_efg_percent = 0.535
        team_turnover_percent = 0.118; opponent_turnover_percent = 0.136; team_offensive_rebound_percent = 0.285
        opponent_offensive_rebound_percent = 0.245; team_free_throw_rate = 0.235; opponent_free_throw_rate = 0.205
        key_player_usage_available = $true; minutes_projection_available = $true; injury_report_status = "clean"
    }
    return New-LiveTicketBase -Sport "nba" -League "NBA" -Event "Knicks at Celtics" -Selection "Celtics" -InputStats $stats
}

function New-NflPayload {
    $stats = @{
        team_name = "Bills"; opponent_name = "Jets"; selection_name = "Bills"; game = "Jets at Bills"; home_away = "home"
        team_offensive_epa_per_play = 0.12; opponent_offensive_epa_per_play = 0.03; team_defensive_epa_per_play = -0.04
        opponent_defensive_epa_per_play = 0.02; team_success_rate = 0.47; opponent_success_rate = 0.42
        team_defensive_success_rate_allowed = 0.40; opponent_defensive_success_rate_allowed = 0.44
        team_explosive_play_rate = 0.12; opponent_explosive_play_rate = 0.09; team_explosive_play_rate_allowed = 0.09
        opponent_explosive_play_rate_allowed = 0.11; team_turnover_rate = 0.09; opponent_turnover_rate = 0.12
        team_pressure_rate_allowed = 0.28; opponent_pressure_rate_allowed = 0.34; team_pressure_rate_generated = 0.36
        opponent_pressure_rate_generated = 0.29; team_red_zone_td_rate = 0.62; opponent_red_zone_td_rate = 0.54
        team_red_zone_td_rate_allowed = 0.50; opponent_red_zone_td_rate_allowed = 0.58; team_pace_seconds_per_play = 27.5
        opponent_pace_seconds_per_play = 29.0; qb_status = "healthy"; offensive_line_health = "good"; injury_report_status = "clean"
    }
    return New-LiveTicketBase -Sport "nfl" -League "NFL" -Event "Jets at Bills" -Selection "Bills" -InputStats $stats
}

function New-MlbPayload {
    $stats = @{
        team_name = "Dodgers"; opponent_name = "Giants"; selection_name = "Dodgers"; game = "Giants at Dodgers"; home_away = "home"; market_name = "moneyline"
        team_projected_runs = 4.8; opponent_projected_runs = 4.1; team_starting_pitcher = "Dodgers SP"; opponent_starting_pitcher = "Giants SP"
        team_starting_pitcher_era = 3.2; opponent_starting_pitcher_era = 4.2; team_starting_pitcher_fip = 3.3; opponent_starting_pitcher_fip = 4.4
        team_starting_pitcher_xfip = 3.4; opponent_starting_pitcher_xfip = 4.3; team_starting_pitcher_k_rate = 0.27; opponent_starting_pitcher_k_rate = 0.22
        team_starting_pitcher_bb_rate = 0.07; opponent_starting_pitcher_bb_rate = 0.09; team_starting_pitcher_hr_rate = 0.9; opponent_starting_pitcher_hr_rate = 1.2
        team_starting_pitcher_innings_projection = 5.8; opponent_starting_pitcher_innings_projection = 5.1; team_bullpen_era = 3.6; opponent_bullpen_era = 4.3
        team_bullpen_fip = 3.7; opponent_bullpen_fip = 4.2; team_bullpen_recent_usage = 2.0; opponent_bullpen_recent_usage = 3.2
        team_bullpen_rest_status = "rested"; opponent_bullpen_rest_status = "tired"; team_woba = 0.335; opponent_woba = 0.310
        team_xwoba = 0.340; opponent_xwoba = 0.315; team_wrc_plus = 112; opponent_wrc_plus = 96; team_iso = 0.180; opponent_iso = 0.145
        team_k_rate = 0.21; opponent_k_rate = 0.24; team_bb_rate = 0.09; opponent_bb_rate = 0.075; park_factor_runs = 1.02
        park_factor_home_runs = 1.05; weather_temperature = 74; weather_wind_mph = 8; weather_wind_direction = "left to right"; roof_status = "open"; injury_report_status = "clean"; lineup_status = "confirmed"
    }
    return New-LiveTicketBase -Sport "mlb" -League "MLB" -Event "Giants at Dodgers" -Selection "Dodgers" -InputStats $stats
}

function New-SoccerPayload {
    $stats = @{
        team = "Arsenal"; opponent = "Chelsea"; selection = "Arsenal"; matchup = "Arsenal vs Chelsea"; home_away = "home"
        market = "three_way_moneyline"; league = "soccer_epl"; match_date = "2026-08-15"
        team_expected_goals = 1.75; opponent_expected_goals = 1.05; team_xg_for = 1.80; opponent_xg_for = 1.20
        team_xg_against = 1.05; opponent_xg_against = 1.45; team_goals_for_per_match = 2.0; opponent_goals_for_per_match = 1.35
        team_goals_against_per_match = 0.95; opponent_goals_against_per_match = 1.45
        team_shots_per_match = 15.2; opponent_shots_per_match = 11.3; team_shots_allowed_per_match = 9.2; opponent_shots_allowed_per_match = 13.4
        team_shots_on_target_per_match = 5.8; opponent_shots_on_target_per_match = 4.1
        team_shots_on_target_allowed_per_match = 3.1; opponent_shots_on_target_allowed_per_match = 4.9
        team_big_chances_per_match = 2.8; opponent_big_chances_per_match = 1.7
        team_big_chances_allowed_per_match = 1.2; opponent_big_chances_allowed_per_match = 2.2
        team_possession_percent = 58; opponent_possession_percent = 49
        team_recent_form_points = 12; opponent_recent_form_points = 8; team_rest_days = 6; opponent_rest_days = 4
        injury_report_status = "clean"; lineup_status = "confirmed"; best_available_odds = 100; book_count = 8; current_odds = 100; consensus_odds = 100
        team_recent_xg_for_5 = 1.9; opponent_recent_xg_for_5 = 1.15; team_recent_xg_against_5 = 0.95; opponent_recent_xg_against_5 = 1.55
    }
    return New-LiveTicketBase -Sport "soccer" -League "EPL" -Event "Arsenal vs Chelsea" -Market "three_way_moneyline" -Selection "Arsenal" -InputStats $stats
}

function New-NhlPayload {
    $stats = @{
        team = "Rangers"; opponent = "Bruins"; selection = "Rangers"; game = "Bruins at Rangers"; home_away = "home"
        market = "moneyline"; league = "nhl"; game_date = "2026-11-12"
        team_projected_goals = 3.35; opponent_projected_goals = 2.75
        team_xg_for_per_game = 3.25; opponent_xg_for_per_game = 2.85
        team_xg_against_per_game = 2.70; opponent_xg_against_per_game = 3.05
        team_goals_for_per_game = 3.30; opponent_goals_for_per_match = 2.90; opponent_goals_for_per_game = 2.90
        team_goals_against_per_game = 2.65; opponent_goals_against_per_game = 3.10
        team_shots_for_per_game = 32.0; opponent_shots_for_per_game = 29.0
        team_shots_against_per_game = 28.0; opponent_shots_against_per_game = 31.0
        team_scoring_chances_for_per_game = 29.0; opponent_scoring_chances_for_per_game = 25.0
        team_scoring_chances_against_per_game = 24.0; opponent_scoring_chances_against_per_game = 28.0
        team_high_danger_chances_for_per_game = 12.0; opponent_high_danger_chances_for_per_game = 9.0
        team_high_danger_chances_against_per_game = 8.0; opponent_high_danger_chances_against_per_game = 11.0
        team_power_play_percent = 24.0; opponent_power_play_percent = 19.0
        team_penalty_kill_percent = 83.0; opponent_penalty_kill_percent = 77.0
        team_recent_form_points = 8; opponent_recent_form_points = 5
        team_rest_days = 2; opponent_rest_days = 1
        team_goalie_confirmed = $true; opponent_goalie_confirmed = $true
        team_starting_goalie_save_percent = 0.918; opponent_starting_goalie_save_percent = 0.904
        team_starting_goalie_gsaax = 6.0; opponent_starting_goalie_gsaax = -2.0
        injury_report_status = "clean"; lineup_status = "confirmed"
        best_available_odds = 100; current_odds = 100; consensus_odds = 100; book_count = 8
    }
    return New-LiveTicketBase -Sport "nhl" -League "NHL" -Event "Bruins at Rangers" -Selection "Rangers" -InputStats $stats
}

function New-TennisPayload {
    $stats = @{
        player = "Novak Djokovic"; opponent = "Carlos Alcaraz"; tournament = "Wimbledon"; match_date = "2026-05-26"; surface = "grass"; best_of_sets = 3
        player_rank = 2; opponent_rank = 3; player_elo = 2200; opponent_elo = 2075; player_recent_win_percent = 80; opponent_recent_win_percent = 70
        player_fatigue_rating = 20; opponent_fatigue_rating = 35; player_days_rest = 4; opponent_days_rest = 3
        player_serve_hold_percent = 86; opponent_serve_hold_percent = 82; player_first_serve_percent = 65; opponent_first_serve_percent = 63
    }
    return New-LiveTicketBase -Sport "tennis" -League "ATP" -Event "Novak Djokovic vs Carlos Alcaraz" -Selection "Novak Djokovic" -InputStats $stats
}

function New-CombatPayload {
    $stats = @{
        fighter = "Jon Jones"; opponent = "Stipe Miocic"; fight_date = "2026-06-01"; promotion = "UFC"; weight_class = "Heavyweight"; scheduled_rounds = 5
        fighter_moneyline = 100; fighter_elo = 2180; opponent_elo = 1980; fighter_recent_win_percent = 90; opponent_recent_win_percent = 70
        fighter_finish_rate = 0.68; opponent_finish_rate = 0.58; fighter_ko_tko_rate = 0.36; opponent_ko_tko_rate = 0.44
        fighter_submission_rate = 0.32; opponent_submission_rate = 0.06; fighter_decision_rate = 0.32; opponent_decision_rate = 0.50
        fighter_strikes_landed_per_min = 4.4; opponent_strikes_landed_per_min = 4.1; fighter_strikes_absorbed_per_min = 2.2; opponent_strikes_absorbed_per_min = 3.7
        fighter_striking_accuracy = 58; opponent_striking_accuracy = 51; fighter_striking_defense = 64; opponent_striking_defense = 56
        fighter_takedown_average = 2.1; opponent_takedown_average = 1.2; fighter_takedown_accuracy = 46; opponent_takedown_accuracy = 34
        fighter_takedown_defense = 95; opponent_takedown_defense = 68; fighter_submission_average = 1.0; opponent_submission_average = 0.2
        fighter_age = 38; opponent_age = 43; fighter_reach = 84.5; opponent_reach = 80; fighter_height = 76; opponent_height = 76
        fighter_stance = "orthodox"; opponent_stance = "orthodox"; fighter_days_rest = 180; opponent_days_rest = 240
        fighter_injury_status = "healthy"; opponent_injury_status = "healthy"
    }
    return New-LiveTicketBase -Sport "ufc" -League "UFC" -Event "Jon Jones vs Stipe Miocic" -Selection "Jon Jones" -InputStats $stats
}

function New-GolfPayload {
    $stats = @{
        golfer = "Scottie Scheffler"; tournament = "Masters Tournament"; course_name = "Augusta National"; field = 89
        world_rank = 1; sg_total = 2.65; sg_off_tee = 0.85; sg_approach = 1.15; sg_around_green = 0.32; sg_putting = 0.33
        recent_form_rank = 2; scoring_average = 68.9; fit_score = 92; history_score = 88; field_strength = 91
        projected_cut_line = 2; wind_rating = 4; difficulty_rating = 8
    }
    return New-LiveTicketBase -Sport "golf" -League "PGA" -Event "Masters Tournament" -Market "top_10" -Selection "Scottie Scheffler" -InputStats $stats
}

function New-WnbaPayload {
    $stats = @{
        game = "Aces at Liberty"; home = "Liberty"; away = "Aces"; team_name = "Liberty"; opponent_name = "Aces"; favorite = "Liberty"
        home_off_rating = 108.5; home_def_rating = 96.2; away_off_rating = 103.1; away_def_rating = 101.8
        home_pace = 79.4; away_pace = 77.8; home_efg = 52.8; away_efg = 49.6; home_tov = 13.1; away_tov = 14.4
        home_oreb = 51.5; away_oreb = 48.7; home_ft_rate = 25.5; away_ft_rate = 22.1; home_injury_adjustment = 0.2
        away_injury_adjustment = -0.6; home_rest_days = 3; away_rest_days = 2; home_travel_fatigue = 0.1; away_travel_fatigue = 0.8; book_count = 8
    }
    return New-LiveTicketBase -Sport "wnba" -League "WNBA" -Event "Aces at Liberty" -Selection "Liberty" -InputStats $stats
}

function New-NcaabPayload {
    $stats = @{
        matchup = "Duke vs North Carolina"; home = "Duke"; away = "North Carolina"; team_name = "Duke"; opponent_name = "North Carolina"; pick = "Duke"
        home_off_rating = 116.0; home_def_rating = 94.5; away_off_rating = 111.0; away_def_rating = 99.0
        home_pace = 70.5; away_pace = 69.1; home_efg = 54.0; away_efg = 50.4; home_tov = 13.0; away_tov = 15.2
        home_oreb = 53.0; away_oreb = 49.5; home_ft_rate = 31.0; away_ft_rate = 27.5; home_rest_days = 5; away_rest_days = 3
        home_travel_fatigue = 0.0; away_travel_fatigue = 0.4; home_ap_rank = 4; away_ap_rank = 16; home_kenpom_rating = 28.5
        away_kenpom_rating = 20.0; home_conference_rating = 8.5; away_conference_rating = 7.8; home_experience = 6.2
        away_experience = 5.1; home_3p_rate = 38.5; away_3p_rate = 34.1; home_ft_pct = 76.0; away_ft_pct = 71.5; book_count = 8
    }
    return New-LiveTicketBase -Sport "ncaab" -League "NCAAB" -Event "Duke vs North Carolina" -Selection "Duke" -InputStats $stats
}

function New-NcaawbPayload {
    $stats = @{
        matchup = "UConn vs South Carolina"; home = "South Carolina"; away = "UConn"; team_name = "South Carolina"; opponent_name = "UConn"; pick = "South Carolina"
        home_off_rating = 114.0; home_def_rating = 88.0; away_off_rating = 108.0; away_def_rating = 94.5
        home_pace = 72.2; away_pace = 70.4; home_efg = 53.5; away_efg = 49.8; home_tov = 12.5; away_tov = 14.0
        home_oreb = 56.0; away_oreb = 50.1; home_ft_rate = 28.0; away_ft_rate = 24.4; home_rest_days = 4; away_rest_days = 3
        home_travel_fatigue = 0.0; away_travel_fatigue = 0.3; home_ap_rank = 1; away_ap_rank = 7; home_net_rating = 31.0
        away_net_rating = 23.0; home_conference_rating = 8.8; away_conference_rating = 8.1; home_experience = 6.8
        away_experience = 6.0; home_3p_rate = 36.5; away_3p_rate = 33.2; home_ft_pct = 75.5; away_ft_pct = 72.0; book_count = 8
    }
    return New-LiveTicketBase -Sport "ncaawb" -League "NCAAWB" -Event "UConn vs South Carolina" -Selection "South Carolina" -InputStats $stats
}

function New-NcaafPayload {
    $stats = @{
        game = "Ohio State vs Michigan"; home = "Ohio State"; away = "Michigan"; team_name = "Ohio State"; opponent_name = "Michigan"; favorite = "Ohio State"
        home_epa_off = 0.23; away_epa_off = 0.15; home_epa_def = -0.08; away_epa_def = -0.02
        home_sr = 0.49; away_sr = 0.44; home_def_sr_allowed = 0.37; away_def_sr_allowed = 0.41
        home_explosive_rate = 0.18; away_explosive_rate = 0.14; home_explosive_allowed = 0.10; away_explosive_allowed = 0.13
        home_pace = 25.4; away_pace = 27.6; home_plays_per_game = 73; away_plays_per_game = 69
        home_ppd = 2.95; away_ppd = 2.45; home_ppd_allowed = 1.55; away_ppd_allowed = 1.92
        home_rz_td = 0.68; away_rz_td = 0.58; home_rz_td_allowed = 0.44; away_rz_td_allowed = 0.52
        home_turnover_margin = 0.6; away_turnover_margin = 0.1; home_havoc_rate = 19.0; away_havoc_rate = 16.0
        home_havoc_allowed = 12.0; away_havoc_allowed = 15.0; home_qb = 88.0; away_qb = 79.0; home_qb_injury = 0.0; away_qb_injury = -0.5
        home_ol = 86.0; away_ol = 78.0; home_dl = 88.0; away_dl = 80.0; home_st = 74.0; away_st = 70.0
        home_field_advantage = 3.0; neutral_site = $false; wind_mph = 6; precipitation = "none"; home_rest_days = 7; away_rest_days = 6
        home_travel_fatigue = 0.0; away_travel_fatigue = 0.6; home_strength_of_schedule = 8.6; away_strength_of_schedule = 8.1
        home_ap_rank = 2; away_ap_rank = 8; home_sp_rating = 29.5; away_sp_rating = 21.0; home_conference_rating = 9.0; away_conference_rating = 8.4; book_count = 8
    }
    return New-LiveTicketBase -Sport "ncaaf" -League "NCAAF" -Event "Ohio State vs Michigan" -Selection "Ohio State" -InputStats $stats
}

function New-CricketPayload {
    $stats = @{
        match = "Mumbai Indians vs Chennai Super Kings"; team_name = "Mumbai Indians"; opponent_name = "Chennai Super Kings"
        home = "Mumbai Indians"; away = "Chennai Super Kings"; batting = "Mumbai Indians"; bowling = "Chennai Super Kings"
        format = "ipl"; ground = "Wankhede Stadium"; surface = "balanced"; weather = "humid"; toss = "Mumbai Indians"; decision = "bowl"
        team_bat_rating = 86; opp_bat_rating = 82; team_bowl_rating = 84; opp_bowl_rating = 80
        team_field_rating = 82; opp_field_rating = 78; team_form = 84; opp_form = 77
        team_pp_rr = 9.2; opp_pp_rr = 8.5; team_middle_rr = 8.4; opp_middle_rr = 7.8
        team_death_rr = 11.2; opp_death_rr = 10.1; team_wicket_loss = 0.24; opp_wicket_loss = 0.28
        team_wicket_rate = 0.31; opp_wicket_rate = 0.27; team_boundary_pct = 0.19; opp_boundary_pct = 0.17
        team_dot_pct = 0.34; opp_dot_pct = 0.37; team_chase = 88; opp_chase = 80; team_defend = 82; opp_defend = 79
        venue_avg_score = 174; chase_win_pct = 0.56; spin_assist = 0.48; pace_assist = 0.52; dew = 0.35; wind = 0.12
        player_name = "Rohit Sharma"; player_team = "Mumbai Indians"; role = "batter"; bat_pos = 1
        batting_avg = 31.5; batting_strike_rate = 142; recent_runs = 36; boundary_rate = 0.17; six_rate = 0.06
        fifty_rate = 0.24; hundred_rate = 0.04; duck_rate = 0.08; bowling_avg = 0; economy = 0; bowling_strike_rate = 0
        recent_wickets = 0; overs_proj = 2.0; balls_faced_proj = 24; runs_proj = 34.5; wickets_proj = 1.4
        sixes_proj = 1.6; fours_proj = 3.2; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "cricket" -League "IPL" -Event "Mumbai Indians vs Chennai Super Kings" -Market "match_winner" -Selection "Mumbai Indians" -InputStats $stats
    $payload.visible_markets = @("match_winner", "total_runs", "player_runs")
    return $payload
}

function New-F1Payload {
    $stats = @{
        race = "Monaco Grand Prix"; track = "Circuit de Monaco"; driver_name = "Max Verstappen"; team = "Red Bull Racing"
        opponent_name = "Charles Leclerc"; opponent_team = "Ferrari"; session_type = "race"; track_type = "street"
        track_km = 3.337; race_laps = 78; weather = "dry"; rain_pct = 0.12; temp_c = 24; wind_kph = 8; track_temp_c = 38
        driver_power_rating = 94; opp_driver_rating = 90; team_pace = 93; opp_team_pace = 89
        car_reliability = 0.95; opp_car_reliability = 0.91; qualy_pace = 92; opp_qualy_pace = 91
        race_pace = 94; opp_race_pace = 89; tire_deg = 87; opp_tire_deg = 82
        pit_rating = 91; opp_pit_rating = 84; strategy = 90; opp_strategy = 84
        dirty_air_sensitivity = 0.34; opponent_dirty_air_sensitivity = 0.42
        overtaking = 89; opp_overtaking = 84; defending = 92; opp_defending = 88
        starts = 90; opp_starts = 86; wet_rating = 93; opp_wet_rating = 88
        street_rating = 88; opp_street_rating = 93; recent_form = 91; opp_recent_form = 86
        team_form = 90; opp_team_form = 85; grid_pos = 2; opp_grid_pos = 3; qualy_pos = 2; opp_qualy_pos = 3
        long_run_pace = 93; opp_long_run_pace = 88; short_run_pace = 92; opp_short_run_pace = 91
        dnf_risk = 0.05; opp_dnf_risk = 0.08; penalty = 0.03; opp_penalty = 0.05
        grid_penalty = 0; opp_grid_penalty = 0; crash = 0.06; opp_crash = 0.08
        sc_probability = 0.68; vsc_probability = 0.42; track_position = 0.92; overtake_difficulty = 0.88; pit_delta = 19.5
        constructor_driver_1_rating = 94; constructor_driver_2_rating = 83
        constructor_race_pace_rating = 93; constructor_qualifying_pace_rating = 92
        constructor_reliability_rating = 0.95; constructor_strategy_rating = 90; constructor_pit_crew_rating = 91; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "f1" -League "Formula 1" -Event "Monaco Grand Prix" -Market "head_to_head" -Selection "Max Verstappen" -InputStats $stats
    $payload.visible_markets = @("head_to_head", "podium_finish", "race_winner")
    return $payload
}

function New-LiveActivePayload {
    param([Parameter(Mandatory = $true)] [string] $Sport)
    switch ($Sport.ToLower()) {
        "nba" { return New-NbaPayload }
        "nfl" { return New-NflPayload }
        "mlb" { return New-MlbPayload }
        "soccer" { return New-SoccerPayload }
        "nhl" { return New-NhlPayload }
        "tennis" { return New-TennisPayload }
        "combat" { return New-CombatPayload }
        "ufc" { return New-CombatPayload }
        "golf" { return New-GolfPayload }
        "wnba" { return New-WnbaPayload }
        "ncaab" { return New-NcaabPayload }
        "ncaawb" { return New-NcaawbPayload }
        "ncaaf" { return New-NcaafPayload }
        "f1" { return New-F1Payload }
        "formula1" { return New-F1Payload }
        "cricket" { return New-CricketPayload }
        default { throw "No live active payload builder registered for sport '$Sport'." }
    }
}
