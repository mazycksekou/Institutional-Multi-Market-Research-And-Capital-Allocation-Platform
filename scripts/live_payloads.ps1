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
        team_name = "Avalanche"; opponent_name = "Wild"; selection_name = "Avalanche"; game = "Wild at Avalanche"; home_away = "home"
        team_xg_for = 3.4; opponent_xg_for = 2.7; team_xg_against = 2.5; opponent_xg_against = 3.1
        team_shots_for = 33; opponent_shots_for = 29; team_shots_against = 28; opponent_shots_against = 32
        team_power_play_pct = 24.5; opponent_power_play_pct = 19.0; team_penalty_kill_pct = 82.0; opponent_penalty_kill_pct = 77.5
        team_goalie_save_pct = 0.916; opponent_goalie_save_pct = 0.904; team_rest_days = 2; opponent_rest_days = 1
    }
    return New-LiveTicketBase -Sport "nhl" -League "NHL" -Event "Wild at Avalanche" -Selection "Avalanche" -InputStats $stats
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
        default { throw "No live active payload builder registered for sport '$Sport'." }
    }
}
