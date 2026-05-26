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

function New-NascarPayload {
    $stats = @{
        race = "Daytona 500"; track_name = "Daytona International Speedway"; driver_name = "Kyle Larson"; team_name = "Hendrick Motorsports"
        manufacturer_name = "Chevrolet"; opponent_name = "Denny Hamlin"; opponent_team_name = "Joe Gibbs Racing"; opponent_manufacturer_name = "Toyota"
        race_series = "NASCAR Cup Series"; session = "race"; track_type = "superspeedway"; track_miles = 2.5; laps = 200; distance_miles = 500
        start_pos = 6; opp_start_pos = 15; qual_pos = 6; opp_qual_pos = 15; practice_pos = 4; opp_practice_pos = 16
        single_lap_speed = 189.4; opp_single_lap_speed = 187.8; five_lap_avg = 188.5; opp_five_lap_avg = 187.2
        ten_lap_avg = 187.8; opp_ten_lap_avg = 186.4; fifteen_lap_avg = 187.0; opp_fifteen_lap_avg = 185.9
        driver_power_rating = 94; opp_driver_rating = 88; season_rating = 93; opp_season_rating = 87
        track_history = 88; opp_track_history = 84; track_type_score = 90; opp_track_type_score = 85
        recent_form = 91; opp_recent_form = 86; car_speed = 92; opp_car_speed = 86
        long_run_speed = 91; opp_long_run_speed = 85; short_run_speed = 93; opp_short_run_speed = 86
        clean_air_speed = 91; opp_clean_air_speed = 85; dirty_air_speed = 90; opp_dirty_air_speed = 86
        restart_score = 92; opp_restart_score = 86; passing_score = 91; opp_passing_score = 86
        defense_score = 89; opp_defense_score = 86; tire_mgmt = 90; opp_tire_mgmt = 85
        pit_rating = 91; opp_pit_rating = 85; crew_chief = 91; opp_crew_chief = 85
        strategy = 90; opp_strategy = 85; manufacturer_score = 88; opp_manufacturer_score = 86
        track_position = 0.52; pass_difficulty = 0.44; tire_wear = 0.42; fuel_strategy = 0.56
        pit_sensitivity = 0.48; caution_prob = 0.62; wreck_prob = 0.18; overtime_prob = 0.20
        temp_f = 72; wind_mph = 12; precip_prob = 0.08; track_temp_f = 84; day_night = "day"
        aero = 0.44; drafting = 0.92; pack_variance = 0.82; road_skill = 0.28; contact_variance = 0.42; aero_variance = 0.44
        dnf_risk = 0.08; opp_dnf_risk = 0.11; mechanical_risk = 0.05; opp_mechanical_risk = 0.08
        crash = 0.10; opp_crash = 0.14; penalty = 0.04; opp_penalty = 0.06; inspection = 0.03; opp_inspection = 0.05
        backup = $false; opp_backup = $false; engine_penalty = $false; opp_engine_penalty = $false; rear_start = $false; opp_rear_start = $false
        field = 36; playoff = $false; elimination = $false; superspeedway = $true; road_course = $false; short_track = $false; intermediate = $false; restrictor_plate = $true
        team_momentum = 88; opp_team_momentum = 85
        manufacturer_speed_rating = 89; manufacturer_reliability_rating = 87; manufacturer_track_type_rating = 88
        manufacturer_recent_form_rating = 87; manufacturer_driver_depth_rating = 86; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "nascar" -League "NASCAR Cup Series" -Event "Daytona 500" -Market "driver_matchup" -Selection "Kyle Larson" -InputStats $stats
    $payload.visible_markets = @("driver_matchup", "top_10_finish", "race_winner")
    return $payload
}

function New-IndyCarPayload {
    $stats = @{
        race = "Indianapolis 500"; track_name = "Indianapolis Motor Speedway"; driver_name = "Alex Palou"; team_name = "Chip Ganassi Racing"
        manufacturer_name = "Honda"; opponent_name = "Josef Newgarden"; opponent_team_name = "Team Penske"; opponent_manufacturer_name = "Chevrolet"
        race_series = "indycar"; session = "race"; track_type = "superspeedway"; track_miles = 2.5; laps = 200; distance_miles = 500
        start_pos = 5; opp_start_pos = 12; qual_pos = 5; opp_qual_pos = 12; practice_pos = 3; opp_practice_pos = 11
        single_lap_speed = 232.4; opp_single_lap_speed = 231.1; five_lap_avg = 231.8; opp_five_lap_avg = 230.5
        ten_lap_avg = 231.2; opp_ten_lap_avg = 229.9; driver_power_rating = 94; opp_driver_rating = 88
        season_rating = 95; opp_season_rating = 87; track_history = 89; opp_track_history = 86
        track_type_score = 91; opp_track_type_score = 86; recent_form = 94; opp_recent_form = 86
        car_speed = 93; opp_car_speed = 87; long_run_speed = 94; opp_long_run_speed = 86
        short_run_speed = 92; opp_short_run_speed = 86; clean_air_speed = 93; opp_clean_air_speed = 87
        traffic_speed = 91; opp_traffic_speed = 85; restart_score = 90; opp_restart_score = 87
        passing_score = 90; opp_passing_score = 86; defense_score = 89; opp_defense_score = 86
        tire_mgmt = 91; opp_tire_mgmt = 85; fuel_save = 94; opp_fuel_save = 86
        pit_rating = 91; opp_pit_rating = 86; strategy = 92; opp_strategy = 86
        manufacturer_score = 88; opp_manufacturer_score = 87; track_position = 0.62; pass_difficulty = 0.48
        tire_wear = 0.40; fuel_strategy = 0.82; pit_sensitivity = 0.58; caution_prob = 0.52
        wreck_prob = 0.18; overtime_prob = 0.16; temp_f = 78; wind_mph = 10; precip_prob = 0.06; track_temp_f = 96
        aero = 0.72; drafting = 0.86; pack_variance = 0.54; road_skill = 0.35; contact_variance = 0.28
        dnf_risk = 0.07; opp_dnf_risk = 0.10; mechanical_risk = 0.04; opp_mechanical_risk = 0.07
        crash = 0.08; opp_crash = 0.11; penalty = 0.03; opp_penalty = 0.05; engine_penalty = 0; opp_engine_penalty = 0
        rear_start = $false; opp_rear_start = $false; field = 33; oval = $true; road_course = $false; street_course = $false
        superspeedway = $true; indy_500_race = $true; team_momentum = 92; opp_team_momentum = 86
        manufacturer_speed_rating = 88; manufacturer_reliability_rating = 0.92; manufacturer_track_type_rating = 88
        manufacturer_recent_form_rating = 89; manufacturer_driver_depth_rating = 87; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "indycar" -League "NTT IndyCar Series" -Event "Indianapolis 500" -Market "driver_matchup" -Selection "Alex Palou" -InputStats $stats
    $payload.visible_markets = @("driver_matchup", "top_10_finish", "race_winner")
    return $payload
}

function New-MotoGPPayload {
    $stats = @{
        race = "Italian Grand Prix"; circuit_name = "Mugello Circuit"; rider_name = "Francesco Bagnaia"; team_name = "Ducati Lenovo Team"
        manufacturer_name = "Ducati"; opponent_name = "Marc Marquez"; opponent_team_name = "Gresini Racing"; opponent_manufacturer_name = "Ducati"
        session_type = "race"; track_type = "flowing"; track_km = 5.245; laps = 23; grid_pos = 2; opp_grid_pos = 5
        qualy_pos = 2; opp_qualy_pos = 5; practice_pos = 2; opp_practice_pos = 6; practice_lap_time = 105.2
        opp_practice_lap_time = 105.7; long_run_pace = 93; opp_long_run_pace = 88; short_run_pace = 92; opp_short_run_pace = 88
        rider_power_rating = 94; opp_rider_rating = 89; season_rating = 93; opp_season_rating = 88
        circuit_history = 92; opp_circuit_history = 88; track_type_score = 91; opp_track_type_score = 87
        recent_form = 92; opp_recent_form = 87; bike_pace = 94; opp_bike_pace = 89
        qualy_pace = 93; opp_qualy_pace = 88; race_pace = 94; opp_race_pace = 88
        tire_deg = 88; opp_tire_deg = 83; braking = 93; opp_braking = 88; cornering = 94; opp_cornering = 88
        launch = 91; opp_launch = 87; overtaking = 90; opp_overtaking = 88; defense_score = 90; opp_defense_score = 88
        wet_rating = 88; opp_wet_rating = 84; manufacturer_score = 92; opp_manufacturer_score = 90
        strategy = 90; opp_strategy = 86; track_position = 0.74; overtake_difficulty = 0.58
        tire_wear = 0.66; front_tire_stress = 0.58; rear_tire_stress = 0.64; crash = 0.08; opp_crash = 0.12
        mechanical_risk = 0.03; opp_mechanical_risk = 0.05; penalty = 0.03; opp_penalty = 0.04
        temp_c = 24; track_temp_c = 38; rain_pct = 0.08; wind_kph = 10; dry_wet_transition_risk = 0.08
        field = 22; sprint_weekend = $true; rider_injury_adjustment = 0; opponent_rider_injury_adjustment = -0.2
        manufacturer_pace_rating = 92; manufacturer_reliability_rating = 0.94; manufacturer_recent_form_rating = 91; manufacturer_rider_depth_rating = 90
        team_rider_1_rating = 94; team_rider_2_rating = 84; team_strategy_rating = 90; team_bike_pace_rating = 93; team_recent_form_rating = 91; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "motogp" -League "MotoGP" -Event "Italian Grand Prix" -Market "rider_matchup" -Selection "Francesco Bagnaia" -InputStats $stats
    $payload.visible_markets = @("rider_matchup", "podium_finish", "race_winner")
    return $payload
}

function New-CS2Payload {
    $stats = @{
        team_name = "Natus Vincere"; opponent_name = "FaZe Clan"; pick = "Natus Vincere"; map = "Mirage"; format = "bo3"; maps = 3
        team_rank = 2; opp_rank = 5; team_elo_rating = 1885; opp_elo_rating = 1810
        team_win_pct = 0.68; opp_win_pct = 0.58; team_round_win_pct = 0.56; opp_round_win_pct = 0.52
        team_ct_pct = 0.58; opp_ct_pct = 0.53; team_t_pct = 0.54; opp_t_pct = 0.50
        team_pistol_pct = 0.57; opp_pistol_pct = 0.51; team_force_buy_pct = 0.38; opp_force_buy_pct = 0.33
        team_eco_pct = 0.20; opp_eco_pct = 0.16; team_anti_eco_pct = 0.82; opp_anti_eco_pct = 0.77
        team_clutch_pct = 0.55; opp_clutch_pct = 0.50; team_entry_pct = 0.54; opp_entry_pct = 0.50
        team_trade_pct = 0.62; opp_trade_pct = 0.57; team_opening_kill_pct = 0.53; opp_opening_kill_pct = 0.49
        team_kast_pct = 75.0; opp_kast_pct = 72.0; team_adr_value = 82.5; opp_adr_value = 78.0
        team_hltv_rating = 1.12; opp_hltv_rating = 1.05; team_util_damage = 24.0; opp_util_damage = 21.0
        team_flash_pct = 0.18; opp_flash_pct = 0.15; team_map_pct = 0.64; opp_map_pct = 0.55
        team_pick_pct = 0.34; opp_pick_pct = 0.28; team_ban_pct = 0.12; opp_ban_pct = 0.18
        ct_bias = 0.54; t_bias = 0.46; team_map_depth = 6; opp_map_depth = 5
        lan = $true; online = $false; tier = "S"; playoff = $true; elimination = $false; region = "EU"
        rest = 3; travel = 0.2; roster_stability_score = 0.92; substitute = 0.02; availability_risk = 0.03
        form = 84; opp_form = 78; market_move = 0.0; public_pct = 52; sharp_pct = 56
        player_name = "s1mple"; role = "AWPer"; player_rating = 1.18; kills_proj = 20.5
        headshots_proj = 7.5; assists_proj = 4.5; deaths_proj = 16.5; kda_proj = 1.45
        adr_proj = 84.5; opening_kills_proj = 3.2; clutches_proj = 0.45; flash_assists_proj = 1.8
        maps_proj = 2.4; prop_line = 18.5; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "cs2" -League "ESL Pro League" -Event "Natus Vincere vs FaZe Clan" -Market "match_winner" -Selection "Natus Vincere" -InputStats $stats
    $payload.visible_markets = @("match_winner", "map_winner", "player_kills")
    return $payload
}

function New-ValorantPayload {
    $stats = @{
        team_name = "Sentinels"; opponent_name = "Fnatic"; pick = "Sentinels"; map = "Ascent"; format = "bo3"; maps = 3
        team_rank = 3; opp_rank = 7; team_elo_rating = 1860; opp_elo_rating = 1795
        team_win_pct = 0.67; opp_win_pct = 0.57; team_round_win_pct = 0.56; opp_round_win_pct = 0.51
        team_attack_pct = 0.55; opp_attack_pct = 0.50; team_defense_pct = 0.57; opp_defense_pct = 0.52
        team_pistol_pct = 0.58; opp_pistol_pct = 0.51; team_bonus_pct = 0.47; opp_bonus_pct = 0.40
        team_eco_pct = 0.19; opp_eco_pct = 0.15; team_anti_eco_pct = 0.83; opp_anti_eco_pct = 0.77
        team_clutch_pct = 0.56; opp_clutch_pct = 0.50; team_first_blood_pct = 0.54; opp_first_blood_pct = 0.49
        team_trade_pct = 0.64; opp_trade_pct = 0.58; team_post_plant_pct = 0.61; opp_post_plant_pct = 0.55
        team_retake_pct = 0.48; opp_retake_pct = 0.43; team_acs_value = 226; opp_acs_value = 213
        team_adr_value = 151; opp_adr_value = 142; team_kast_pct = 76.5; opp_kast_pct = 72.5
        team_vlr_rating = 1.12; opp_vlr_rating = 1.04; team_util_value = 82; opp_util_value = 75
        team_agent_comp = 88; opp_agent_comp = 80; duelist = 90; initiator = 87; controller = 86; sentinel = 84
        team_map_pct = 0.65; opp_map_pct = 0.55; team_pick_pct = 0.35; opp_pick_pct = 0.28
        team_ban_pct = 0.10; opp_ban_pct = 0.17; attack_bias = 0.51; defense_bias = 0.49
        team_map_depth = 6; opp_map_depth = 5; lan = $true; online = $false; tier = "VCT"; playoff = $true
        elimination = $false; region = "NA"; rest = 4; travel = 0.18; roster_stability_score = 0.91
        substitute = 0.02; availability_risk = 0.03; form = 84; opp_form = 77; market_move = 0.0
        public_pct = 53; sharp_pct = 57
        player_name = "zekken"; role = "Duelist"; agent_pool = 88; player_rating = 1.16; kills_proj = 19.5
        assists_proj = 6.5; deaths_proj = 16.5; kda_proj = 1.45; acs_proj = 236; adr_proj = 154
        first_bloods_proj = 3.1; headshots_proj = 7.0; clutches_proj = 0.5; maps_proj = 2.4
        prop_line = 18.5; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "valorant" -League "VCT" -Event "Sentinels vs Fnatic" -Market "match_winner" -Selection "Sentinels" -InputStats $stats
    $payload.visible_markets = @("match_winner", "map_winner", "player_kills")
    return $payload
}

function New-LoLPayload {
    $stats = @{
        team_name = "T1"; opponent_name = "Gen.G"; pick = "T1"; format = "bo3"; maps = 3
        region_name = "lck"; league_name = "LCK"; patch = "14.10"; team_rank = 2; opp_rank = 4
        team_elo_rating = 1875; opp_elo_rating = 1810; team_win_pct = 0.68; opp_win_pct = 0.59
        team_game_win_pct = 0.64; opp_game_win_pct = 0.57; team_blue_pct = 0.61; opp_blue_pct = 0.55
        team_red_pct = 0.58; opp_red_pct = 0.52; team_early = 88; opp_early = 82
        team_mid = 87; opp_mid = 81; team_late = 89; opp_late = 84
        team_gd10 = 420; opp_gd10 = 180; team_gd15 = 760; opp_gd15 = 320
        team_xpd10 = 260; opp_xpd10 = 110; team_xpd15 = 520; opp_xpd15 = 240
        team_first_blood_pct = 0.56; opp_first_blood_pct = 0.50; team_first_tower_pct = 0.59; opp_first_tower_pct = 0.51
        team_first_dragon_pct = 0.57; opp_first_dragon_pct = 0.50; team_first_herald_pct = 0.58; opp_first_herald_pct = 0.49
        team_baron_pct = 0.66; opp_baron_pct = 0.57; team_dragon_pct = 0.64; opp_dragon_pct = 0.55
        team_objective_score = 88; opp_objective_score = 80; team_vision_score = 86; opp_vision_score = 79
        team_kills_per_game = 15.8; opp_kills_per_game = 13.9; team_deaths_per_game = 11.6; opp_deaths_per_game = 12.9
        team_kda_value = 4.1; opp_kda_value = 3.3; team_dpm = 2340; opp_dpm = 2180; team_gpm = 1905; opp_gpm = 1835
        team_draft_score = 89; opp_draft_score = 81; team_champ_pool = 8; opp_champ_pool = 6
        team_meta_fit = 88; opp_meta_fit = 80; top_rating = 86; jungle_rating = 90; mid_rating = 91; adc_rating = 88; support_rating = 87
        opp_top_rating = 82; opp_jungle_rating = 84; opp_mid_rating = 85; opp_adc_rating = 84; opp_support_rating = 82
        roster_stability_score = 0.93; substitute = 0.02; availability_risk = 0.03; rest = 4; travel = 0.15
        lan = $true; online = $false; tier = "major"; playoff = $true; elimination = $false; form = 85; opp_form = 78
        market_move = 0.0; public_pct = 54; sharp_pct = 58
        player_name = "Faker"; role = "mid"; champion_pool = 90; player_meta_fit = 88
        kills_proj = 4.8; assists_proj = 7.4; deaths_proj = 2.1; kda_proj = 5.6; kp_proj = 0.72
        damage_share_proj = 0.27; gold_share_proj = 0.24; maps_proj = 2.4; prop_line = 4.5; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "lol" -League "LCK" -Event "T1 vs Gen.G" -Market "match_winner" -Selection "T1" -InputStats $stats
    $payload.visible_markets = @("match_winner", "game_winner", "player_kills")
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
        "nascar" { return New-NascarPayload }
        "nascar_cup" { return New-NascarPayload }
        "indycar" { return New-IndyCarPayload }
        "indy_car" { return New-IndyCarPayload }
        "motogp" { return New-MotoGPPayload }
        "moto_gp" { return New-MotoGPPayload }
        "cricket" { return New-CricketPayload }
        "cs2" { return New-CS2Payload }
        "counter_strike_2" { return New-CS2Payload }
        "csgo" { return New-CS2Payload }
        "valorant" { return New-ValorantPayload }
        "val" { return New-ValorantPayload }
        "riot_valorant" { return New-ValorantPayload }
        "esports_valorant" { return New-ValorantPayload }
        "vct" { return New-ValorantPayload }
        "valorant_champions_tour" { return New-ValorantPayload }
        "league_of_legends" { return New-LoLPayload }
        "lol" { return New-LoLPayload }
        "league" { return New-LoLPayload }
        "riot_lol" { return New-LoLPayload }
        "esports_lol" { return New-LoLPayload }
        "lcs" { return New-LoLPayload }
        "lec" { return New-LoLPayload }
        "lck" { return New-LoLPayload }
        "lpl" { return New-LoLPayload }
        "worlds" { return New-LoLPayload }
        "msi" { return New-LoLPayload }
        default { throw "No live active payload builder registered for sport '$Sport'." }
    }
}
