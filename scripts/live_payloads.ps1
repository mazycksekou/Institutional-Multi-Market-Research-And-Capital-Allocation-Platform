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

function New-RugbyPayload {
    $stats = @{
        team_name = "Ireland"; opponent_name = "France"; pick = "Ireland"; variant = "rugby_union"; competition_name = "Six Nations"; home = "home"; neutral = $false
        team_power_rating = 91; opp_power_rating = 87; team_elo_rating = 1840; opp_elo_rating = 1785; team_win_pct = 0.74; opp_win_pct = 0.64
        team_form = 88; opp_form = 82; team_pf = 31.4; opp_pf = 28.2; team_pa = 18.6; opp_pa = 21.4
        team_xp_for = 30.8; opp_xp_for = 27.7; team_xp_against = 19.2; opp_xp_against = 22.0
        team_tries = 4.1; opp_tries = 3.6; team_tries_allowed = 2.1; opp_tries_allowed = 2.6
        team_kicking_pct = 0.83; opp_kicking_pct = 0.78; team_set_piece = 90; opp_set_piece = 84
        team_scrum = 88; opp_scrum = 83; team_lineout = 91; opp_lineout = 85; team_ruck = 89; opp_ruck = 84
        team_breakdown = 90; opp_breakdown = 85; team_maul = 87; opp_maul = 82; team_territory = 89; opp_territory = 84
        team_possession = 87; opp_possession = 83; team_kicking_game = 88; opp_kicking_game = 84
        team_discipline = 86; opp_discipline = 80; team_penalties = 8.2; opp_penalties = 10.4
        team_yellow_cards = 0.18; opp_yellow_cards = 0.32; team_red_cards = 0.02; opp_red_cards = 0.05
        team_tackle_pct = 0.89; opp_tackle_pct = 0.85; team_missed_tackles = 13.2; opp_missed_tackles = 16.8
        team_line_breaks = 6.1; opp_line_breaks = 5.0; team_offloads = 8.5; opp_offloads = 7.2
        team_gainline = 0.58; opp_gainline = 0.52; team_turnovers = 10.8; opp_turnovers = 12.5
        team_forced_turnovers = 7.8; opp_forced_turnovers = 6.5; team_goal_line_defense = 88; opp_goal_line_defense = 83
        team_availability = 0.93; opp_availability = 0.88; key_available = 0.95; opp_key_available = 0.89
        rest = 7; opp_rest = 6; travel = 0.08; opp_travel = 0.14; weather_risk = 0.15; rain_pct = 0.12
        wind_kph = 16; temp_c = 12; pitch = "good"; ref_penalty_rate = 19.5; ref_card_rate = 0.42
        market_move = 0.0; public_pct = 54; sharp_pct = 58
        player_name = "James Lowe"; position = "wing"; minutes_proj = 78; try_proj = 0.46; points_proj = 5.2
        tackles_proj = 8.5; kicking_points_proj = 0.0; goal_kicking_pct = 0.0; anytime_try_prob = 0.48; first_try_prob = 0.12
        prop_line = 0.5; book_count = 8; current_odds = 100
    }
    return New-LiveTicketBase -Sport "rugby_union" -League "Six Nations" -Event "Ireland vs France" -Market "match_winner" -Selection "Ireland" -InputStats $stats
}

function New-LacrossePayload {
    $stats = @{
        team_name = "Atlas"; opponent_name = "Whipsnakes"; pick = "Atlas"; competition_name = "PLL"; gender = "mens"; format = "field"; home = "home"; neutral = $false
        team_power_rating = 88; opp_power_rating = 82; team_elo_rating = 1810; opp_elo_rating = 1740; team_win_pct = 0.70; opp_win_pct = 0.58
        team_form = 86; opp_form = 78; team_gf = 13.8; opp_gf = 12.1; team_ga = 10.6; opp_ga = 12.4
        team_xg_for = 13.5; opp_xg_for = 12.0; team_xg_against = 10.8; opp_xg_against = 12.5
        team_shots = 44.0; opp_shots = 39.5; team_sog = 27.0; opp_sog = 23.5; team_shot_quality = 88; opp_shot_quality = 80
        team_save_pct = 0.565; opp_save_pct = 0.520; goalie_score = 86; opp_goalie_score = 78; team_faceoff_pct = 0.585; opp_faceoff_pct = 0.495
        team_possession = 87; opp_possession = 80; team_ground_balls = 34.0; opp_ground_balls = 29.5
        team_turnovers = 12.0; opp_turnovers = 14.4; team_forced_turnovers = 8.1; opp_forced_turnovers = 6.4
        team_clear_pct = 0.885; opp_clear_pct = 0.835; team_ride_pct = 0.185; opp_ride_pct = 0.145
        team_emo = 0.465; opp_emo = 0.380; team_man_down = 0.710; opp_man_down = 0.655
        team_penalties = 2.8; opp_penalties = 3.4; team_transition = 87; opp_transition = 79
        team_set_offense = 86; opp_set_offense = 80; team_def_eff = 84; opp_def_eff = 78
        team_pace_value = 75.0; opp_pace_value = 71.0; team_availability = 0.94; opp_availability = 0.88
        key_available = 0.96; opp_key_available = 0.88; rest = 5; opp_rest = 4; travel = 0.10; opp_travel = 0.22
        weather_risk = 0.10; wind_mph = 8; temp_f = 72; field = "dry"; ref_penalty_rate = 5.6
        market_move = 0.0; public_pct = 52; sharp_pct = 58
        player_name = "Jeff Teat"; position = "attack"; minutes_proj = 48; goals_proj = 2.4; assists_proj = 2.0; points_proj = 4.4
        shots_proj = 8.5; sog_proj = 5.1; saves_proj = 0.0; ground_balls_proj = 2.2; faceoff_wins_proj = 0.0
        anytime_goal_prob = 0.72; first_goal_prob = 0.14; prop_line = 1.5; book_count = 8; current_odds = 100
    }
    $payload = New-LiveTicketBase -Sport "pll" -League "PLL" -Event "Atlas vs Whipsnakes" -Market "match_winner" -Selection "Atlas" -InputStats $stats
    $payload.visible_markets = @("match_winner", "spread", "player_goals")
    return $payload
}

function New-TableTennisPayload {
    $stats = @{
        player_name = "Ma Long"; opponent_name = "Fan Zhendong"; pick = "Ma Long"; tournament_name = "WTT Champions"; competition_name = "WTT"; format = "best_of_7"; games = 7; game_no = 1; neutral = $true
        player_power_rating = 91; opp_power_rating = 87; player_elo_rating = 2185; opp_elo_rating = 2120; player_rank = 3; opp_rank = 5
        player_win_pct = 0.72; opp_win_pct = 0.64; player_form = 88; opp_form = 82
        serve_rating = 90; opp_serve_rating = 85; return_rating = 88; opp_return_rating = 82
        service_points_won_pct = 0.62; opp_service_points_won_pct = 0.58; return_points_won_pct = 0.46; opp_return_points_won_pct = 0.42
        first_ball_attack = 89; opp_first_ball_attack = 83; receive_quality = 88; opp_receive_quality = 82
        rally_rating = 90; opp_rally_rating = 84; short_game = 86; opp_short_game = 82; counterattack = 89; opp_counterattack = 84
        defense = 87; opp_defense = 83; spin = 90; opp_spin = 84; speed = 88; opp_speed = 85; consistency = 89; opp_consistency = 83
        error_rate = 0.12; opp_error_rate = 0.16; game_win_pct = 0.66; opp_game_win_pct = 0.58
        deciding_game_pct = 0.62; opp_deciding_game_pct = 0.54; comeback = 86; opp_comeback = 80; clutch = 88; opp_clutch = 82
        momentum = 87; opp_momentum = 81; pressure = 88; opp_pressure = 82
        handedness = "right_vs_right"; style_matchup = "two-wing attack"; table_speed = 0.55; ball_speed = 0.52; altitude = 120
        fatigue = 0.12; opp_fatigue = 0.18; rest = 3; opp_rest = 2; travel = 0.08; opp_travel = 0.16; injury = 0.04; opp_injury = 0.08
        market_move = 0.0; public_pct = 54; sharp_pct = 58
        points_proj = 47.5; opp_points_proj = 42.0; games_proj = 4.7; opp_games_proj = 3.8; service_points_proj = 28.5; return_points_proj = 19.0
        prop_line = 26.5; book_count = 8; current_odds = 100
    }
    $payload = New-LiveTicketBase -Sport "ping_pong" -League "WTT" -Event "Ma Long vs Fan Zhendong" -Market "match_winner" -Selection "Ma Long" -InputStats $stats
    $payload.visible_markets = @("match_winner", "game_handicap", "player_service_points_won")
    return $payload
}

function New-BadmintonPayload {
    $stats = @{
        player_name = "Viktor Axelsen"; opponent_name = "Lee Zii Jia"; team_name = "Axelsen"; opponent_team_name = "Lee Zii Jia"; pick = "Viktor Axelsen"
        tournament_name = "BWF World Tour Finals"; competition_name = "BWF World Tour"; format = "best_of_3"; games = 3; discipline = "singles"; neutral = $true
        player_power_rating = 91; opp_power_rating = 86; player_elo_rating = 2195; opp_elo_rating = 2110; player_rank = 1; opp_rank = 8
        player_win_pct = 0.76; opp_win_pct = 0.62; player_form = 89; opp_form = 81
        serve_rating = 90; opp_serve_rating = 84; return_rating = 88; opp_return_rating = 82
        service_points_won_pct = 0.64; opp_service_points_won_pct = 0.58; return_points_won_pct = 0.47; opp_return_points_won_pct = 0.41
        short_serve = 89; opp_short_serve = 83; long_serve = 88; opp_long_serve = 82
        rally_rating = 90; opp_rally_rating = 83; net_play = 87; opp_net_play = 82; smash = 91; opp_smash = 85
        drop_shot = 88; opp_drop_shot = 82; clear = 89; opp_clear = 83; defense = 88; opp_defense = 82
        speed = 87; opp_speed = 84; stamina = 89; opp_stamina = 82; error_rate = 0.13; opp_error_rate = 0.18
        game_win_pct = 0.68; opp_game_win_pct = 0.57; deciding_game_pct = 0.64; opp_deciding_game_pct = 0.52
        clutch = 88; opp_clutch = 81; momentum = 87; opp_momentum = 80; pressure = 88; opp_pressure = 81
        handedness = "right_vs_right"; style_matchup = "attacking control"; court_speed = 0.55; shuttle_speed = 0.52; altitude = 90
        fatigue = 0.12; opp_fatigue = 0.20; rest = 3; opp_rest = 2; travel = 0.08; opp_travel = 0.18; injury = 0.03; opp_injury = 0.09
        market_move = 0.0; public_pct = 54; sharp_pct = 58
        points_proj = 45.5; opp_points_proj = 39.5; games_proj = 2.2; opp_games_proj = 1.8; service_points_proj = 27.5; return_points_proj = 18.5
        prop_line = 25.5; book_count = 8; current_odds = 100
    }
    $payload = New-LiveTicketBase -Sport "bwf" -League "BWF World Tour" -Event "Viktor Axelsen vs Lee Zii Jia" -Market "match_winner" -Selection "Viktor Axelsen" -InputStats $stats
    $payload.visible_markets = @("match_winner", "game_handicap", "player_service_points_won")
    return $payload
}

function New-PickleballPayload {
    $stats = @{
        player_name = "Ben Johns"; opponent_name = "Federico Staksrud"; team_name = "Johns"; opponent_team_name = "Staksrud"; pick = "Ben Johns"
        tournament_name = "PPA Tour Finals"; competition_name = "PPA Tour"; format = "best_of_3"; games = 3; discipline = "singles"; court = "indoor"; neutral = $true
        player_power_rating = 92; opp_power_rating = 86; player_elo_rating = 2210; opp_elo_rating = 2120; player_rank = 1; opp_rank = 5
        player_win_pct = 0.78; opp_win_pct = 0.63; player_form = 90; opp_form = 82
        serve_rating = 89; opp_serve_rating = 84; return_rating = 90; opp_return_rating = 83
        service_points_won_pct = 0.66; opp_service_points_won_pct = 0.59; return_points_won_pct = 0.48; opp_return_points_won_pct = 0.42
        third_shot_drop = 91; opp_third_shot_drop = 84; third_shot_drive = 88; opp_third_shot_drive = 83
        dink = 92; opp_dink = 84; kitchen = 91; opp_kitchen = 83; hand_speed = 89; opp_hand_speed = 84
        net_exchange = 90; opp_net_exchange = 83; lob = 85; opp_lob = 82; overhead = 90; opp_overhead = 84
        rally_rating = 91; opp_rally_rating = 83; error_rate = 0.12; opp_error_rate = 0.18
        game_win_pct = 0.69; opp_game_win_pct = 0.57; deciding_game_pct = 0.65; opp_deciding_game_pct = 0.52
        clutch = 89; opp_clutch = 81; momentum = 88; opp_momentum = 80; pressure = 89; opp_pressure = 81
        handedness = "right_vs_right"; style_matchup = "kitchen control"; court_speed = 0.54; ball_speed = 0.50; altitude = 80
        fatigue = 0.10; opp_fatigue = 0.19; rest = 3; opp_rest = 2; travel = 0.07; opp_travel = 0.17; injury = 0.03; opp_injury = 0.08
        market_move = 0.0; public_pct = 54; sharp_pct = 58
        points_proj = 33.5; opp_points_proj = 27.5; games_proj = 2.1; opp_games_proj = 1.7; service_points_proj = 20.5; return_points_proj = 13.5
        prop_line = 18.5; book_count = 8; current_odds = 100
    }
    $payload = New-LiveTicketBase -Sport "ppa" -League "PPA Tour" -Event "Ben Johns vs Federico Staksrud" -Market "match_winner" -Selection "Ben Johns" -InputStats $stats
    $payload.visible_markets = @("match_winner", "game_handicap", "player_service_points_won")
    return $payload
}

function New-VolleyballPayload {
    $stats = @{
        team_name = "Nebraska"; opponent_name = "Wisconsin"; pick = "Nebraska"; competition_name = "NCAA"; format = "best_of_5"; sets = 5
        court = "indoor"; gender = "womens"; home = "home"; neutral = $false
        team_power_rating = 91; opp_power_rating = 86; team_elo_rating = 1885; opp_elo_rating = 1810; team_win_pct = 0.78; opp_win_pct = 0.66; team_form = 89; opp_form = 82
        team_attack = 90; opp_attack = 85; team_kill_pct = 0.42; opp_kill_pct = 0.38; team_hit_pct = 0.298; opp_hit_pct = 0.247; team_sideout_pct = 0.65; opp_sideout_pct = 0.59
        team_transition_attack = 88; opp_transition_attack = 82; team_error_pct = 0.16; opp_error_pct = 0.20
        team_serve = 87; opp_serve = 82; team_ace_pct = 0.082; opp_ace_pct = 0.064; team_service_error_pct = 0.11; opp_service_error_pct = 0.13
        team_receive = 88; opp_receive = 82; team_pass = 89; opp_pass = 83; team_first_contact = 88; opp_first_contact = 82
        team_block = 86; opp_block = 80; team_block_pct = 0.14; opp_block_pct = 0.11; team_digs = 16.5; opp_digs = 14.2; team_defense = 88; opp_defense = 82; team_floor_defense = 87; opp_floor_defense = 81
        team_set_win_pct = 0.68; opp_set_win_pct = 0.57; team_deciding_set_pct = 0.62; opp_deciding_set_pct = 0.51; team_clutch = 88; opp_clutch = 81; team_momentum = 87; opp_momentum = 80
        team_availability = 0.94; opp_availability = 0.88; key_available = 0.96; opp_key_available = 0.90; rest = 4; opp_rest = 3; travel = 0.06; opp_travel = 0.14; altitude = 0.12; venue = 0.65
        market_move = 0.0; public_pct = 54; sharp_pct = 58
        player_name = "Merritt Beason"; position = "outside"; sets_proj = 4.2; kills_proj = 17.5; aces_proj = 1.4; blocks_proj = 2.6; digs_proj = 9.5; assists_proj = 0.8; points_proj = 21.5; prop_line = 16.5
        book_count = 8; current_odds = 100
    }
    $payload = New-LiveTicketBase -Sport "vnl" -League "NCAA" -Event "Nebraska vs Wisconsin" -Market "match_winner" -Selection "Nebraska" -InputStats $stats
    $payload.visible_markets = @("match_winner", "set_handicap", "player_kills")
    return $payload
}

function New-HandballPayload {
    $stats = @{
        team_name = "Kiel"; opponent_name = "Barcelona"; pick = "Kiel"; competition_name = "EHF Champions League"; home = "home"; neutral = $false
        team_power_rating = 90; opp_power_rating = 85; team_elo_rating = 1845; opp_elo_rating = 1780; team_win_pct = 0.72; opp_win_pct = 0.64; team_form = 88; opp_form = 82
        team_gf = 32.4; opp_gf = 30.8; team_ga = 27.6; opp_ga = 29.4; team_xg_for = 31.8; opp_xg_for = 30.1; team_xg_against = 27.9; opp_xg_against = 29.2
        team_shots = 52.0; opp_shots = 49.5; team_shot_pct = 0.62; opp_shot_pct = 0.59; team_attack_eff = 0.64; opp_attack_eff = 0.59; team_7m_pct = 0.82; opp_7m_pct = 0.76
        team_def_eff = 0.78; opp_def_eff = 0.73; gk_save_pct = 0.345; opp_gk_save_pct = 0.318; gk_rating = 88; opp_gk_rating = 82; team_blocks = 3.8; opp_blocks = 3.1; team_steals = 5.6; opp_steals = 4.9
        team_pace_value = 61.5; opp_pace_value = 59.8; team_fastbreak_pct = 0.18; opp_fastbreak_pct = 0.14; team_fastbreak_eff = 0.72; opp_fastbreak_eff = 0.65
        team_turnovers = 10.6; opp_turnovers = 12.2; team_forced_turnovers = 11.8; opp_forced_turnovers = 10.1; team_possession_eff = 0.61; opp_possession_eff = 0.57
        team_penalties = 3.2; opp_penalties = 3.8; team_2min = 2.4; opp_2min = 3.1; team_availability = 0.94; opp_availability = 0.88; key_available = 0.96; opp_key_available = 0.90
        rest = 5; opp_rest = 4; travel = 0.08; opp_travel = 0.18; venue = 0.70; ref_penalty_rate = 7.2; market_move = 0.0; public_pct = 54; sharp_pct = 58
        player_name = "Sander Sagosen"; position = "back"; minutes_proj = 48; goals_proj = 6.4; assists_proj = 4.2; saves_proj = 0.0; shots_proj = 9.5; points_proj = 10.6
        anytime_goal_prob = 0.82; first_goal_prob = 0.10; prop_line = 5.5; book_count = 8; current_odds = 100
    }
    $payload = New-LiveTicketBase -Sport "ehf" -League "EHF Champions League" -Event "Kiel vs Barcelona" -Market "match_winner" -Selection "Kiel" -InputStats $stats
    $payload.visible_markets = @("match_winner", "spread", "player_goals")
    return $payload
}

function New-WaterPoloPayload {
    $stats = @{
        team_name = "Hungary"; opponent_name = "Spain"; pick = "Hungary"; competition_name = "World Aquatics"; gender = "mens"; format = "outdoor"; home = "home"; neutral = $false
        venue_name = "Aquatics Centre"; pool_type = "50m"; team_power_rating = 90; opp_power_rating = 86; team_elo_rating = 1845; opp_elo_rating = 1790
        team_win_pct = 0.74; opp_win_pct = 0.66; team_form = 88; opp_form = 82; team_gf = 13.2; opp_gf = 12.4; team_ga = 9.6; opp_ga = 10.4
        team_xg_for = 13.0; opp_xg_for = 12.0; team_xg_against = 9.8; opp_xg_against = 10.7; team_shots = 31.0; opp_shots = 29.0
        team_shot_pct = 0.42; opp_shot_pct = 0.39; team_shot_quality = 88; opp_shot_quality = 83; gk_save_pct = 0.58; opp_gk_save_pct = 0.54
        gk_rating = 89; opp_gk_rating = 84; team_def_eff = 0.82; opp_def_eff = 0.77; team_blocks = 4.1; opp_blocks = 3.4; team_steals = 6.2; opp_steals = 5.4
        team_pp_conv = 0.41; opp_pp_conv = 0.36; team_pk = 0.79; opp_pk = 0.74; team_excl = 8.8; opp_excl = 10.2; team_drawn_excl = 10.0; opp_drawn_excl = 9.1
        team_pace_value = 60.5; opp_pace_value = 58.8; team_possession_eff = 0.61; opp_possession_eff = 0.57; team_counterattack_rate = 0.17; opp_counterattack_rate = 0.13
        team_counterattack_eff = 0.68; opp_counterattack_eff = 0.60; team_turnovers = 11.2; opp_turnovers = 12.6; team_forced_turnovers = 12.3; opp_forced_turnovers = 10.8
        team_center_forward_rating = 88; opp_center_forward_rating = 83; team_perimeter_shooting_rating = 87; opp_perimeter_shooting_rating = 82
        team_swim_speed_rating = 86; opp_swim_speed_rating = 81; team_availability = 0.95; opp_availability = 0.90; key_available = 0.96; opp_key_available = 0.90
        rest = 4; opp_rest = 3; travel = 0.08; opp_travel = 0.16; ref_exclusion_rate = 11.8; market_move = 0.0; public_pct = 54; sharp_pct = 58
        player_name = "Denes Varga"; position = "attacker"; minutes_proj = 28; goals_proj = 2.6; assists_proj = 1.5; shots_proj = 6.2; saves_proj = 0.0
        points_proj = 4.1; anytime_goal_prob = 0.78; first_goal_prob = 0.12; prop_line = 1.5; book_count = 8; current_odds = 100
    }
    $payload = New-LiveTicketBase -Sport "water_polo" -League "World Aquatics" -Event "Hungary vs Spain" -Market "match_winner" -Selection "Hungary" -InputStats $stats
    $payload.visible_markets = @("match_winner", "spread", "player_goals")
    return $payload
}

function New-AFLPayload {
    $stats = @{
        team_name = "Collingwood"; opponent_name = "Carlton"; pick = "Collingwood"; competition_name = "AFL"; venue_name = "MCG"; home = "home"; neutral = $false
        team_power_rating = 88; opp_power_rating = 82; team_elo_rating = 1815; opp_elo_rating = 1750; team_win_pct = 0.70; opp_win_pct = 0.58
        team_form = 86; opp_form = 78; team_pf = 91.5; opp_pf = 84.2; team_pa = 75.4; opp_pa = 83.6
        team_xscore_for = 93.0; opp_xscore_for = 84.0; team_xscore_against = 76.0; opp_xscore_against = 85.0
        team_goal_accuracy_pct = 0.535; opp_goal_accuracy_pct = 0.492; team_scoring_shots = 26.5; opp_scoring_shots = 23.2
        team_inside50s = 58.0; opp_inside50s = 51.0; team_i50_conversion = 0.47; opp_i50_conversion = 0.41
        team_clearances = 42.0; opp_clearances = 36.0; team_center_clearances = 13.5; opp_center_clearances = 10.8
        team_stoppage_clearances = 28.5; opp_stoppage_clearances = 25.2; team_contested_possessions = 144.0; opp_contested_possessions = 134.0
        team_uncontested_possessions = 235.0; opp_uncontested_possessions = 221.0; team_disposal_eff_pct = 0.742; opp_disposal_eff_pct = 0.706
        team_turnovers = 59.0; opp_turnovers = 65.0; team_intercept_marks = 15.2; opp_intercept_marks = 12.8
        team_marks_i50 = 13.0; opp_marks_i50 = 10.6; team_tackles = 68.0; opp_tackles = 61.0
        team_pressure = 87; opp_pressure = 80; team_rebound50s = 39.0; opp_rebound50s = 34.0
        team_ruck = 86; opp_ruck = 78; team_hitout_pct = 0.56; opp_hitout_pct = 0.48
        team_availability = 0.94; opp_availability = 0.88; key_available = 0.96; opp_key_available = 0.89
        rest = 7; opp_rest = 6; travel = 0.08; opp_travel = 0.16; weather_risk = 0.12
        rain_pct = 0.10; wind_kph = 16; temp_c = 17; ground = "firm"; umpire_fk_rate = 39.5
        market_move = 0.0; public_pct = 52; sharp_pct = 58
        player_name = "Nick Daicos"; position = "midfielder"; minutes_proj = 86; goals_proj = 1.1; disposals_proj = 31.5
        marks_proj = 6.2; tackles_proj = 5.8; hitouts_proj = 0.0; fantasy_points_proj = 111.0
        anytime_goal_prob = 0.56; first_goal_prob = 0.08; prop_line = 27.5; book_count = 8; current_odds = 100
    }
    $payload = New-LiveTicketBase -Sport "aussie_rules" -League "AFL" -Event "Collingwood vs Carlton" -Market "match_winner" -Selection "Collingwood" -InputStats $stats
    $payload.visible_markets = @("match_winner", "spread", "player_disposals")
    return $payload
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

function New-FormulaEPayload {
    $stats = @{
        driver_name = "Jake Dennis"; team_name = "Andretti"; opponent_name = "Pascal Wehrlein"; opponent_team_name = "Porsche"
        track = "Monaco E-Prix Circuit"; track_type = "street"; street = $true; race_no = 8
        qualy_pos = 3; grid_pos = 3; driver_power_rating = 91; opp_driver_rating = 88
        team_power_rating = 89; opp_team_power_rating = 87; form = 88; opp_form = 84
        points = 112; opp_points = 104; champ_pos = 2; opp_champ_pos = 4
        qualy_pace = 90; opp_qualy_pace = 87; race_pace = 91; opp_race_pace = 86
        energy_rating = 93; opp_energy_rating = 87; attack_eff = 0.86; opp_attack_eff = 0.80
        regen = 0.91; opp_regen = 0.85; efficiency = 92; opp_efficiency = 86
        street_rating = 90; opp_street_rating = 85; overtaking = 86; opp_overtaking = 82
        defense = 88; opp_defense = 84; tire_mgmt = 86; opp_tire_mgmt = 83
        racecraft = 90; opp_racecraft = 86; qualy_h2h = 0.58; race_h2h = 0.61
        reliability = 0.94; opp_reliability = 0.90; dnf_risk = 0.05; opp_dnf_risk = 0.08
        penalty = 0.04; opp_penalty = 0.07; incident = 0.06; opp_incident = 0.09
        sc_probability = 0.58; fcy_probability = 0.36; weather_risk = 0.12; rain_pct = 0.08
        track_temp = 31; air_temp = 23; humidity_pct = 55; wind_kph = 12
        practice_rank = 4; opp_practice_rank = 8; qualy_delta = -0.04; race_delta = -0.08
        grid_penalty = 0; opp_grid_penalty = 0; attack_count = 2; attack_loss = 1.7
        pit_boost = $true; battery_temp_risk = 0.10; efficiency_window = 91
        market_move = 0.0; public_pct = 53; sharp_pct = 57; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "formula_e" -League "Formula E" -Event "Monaco E-Prix" -Market "race_head_to_head" -Selection "Jake Dennis" -InputStats $stats
    $payload.visible_markets = @("race_head_to_head", "podium_finish", "race_winner")
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

function New-Dota2Payload {
    $stats = @{
        team_name = "Team Liquid"; opponent_name = "Gaimin Gladiators"; pick = "Team Liquid"; format = "bo3"; maps = 3
        region_name = "western_europe"; league_name = "The International"; patch = "7.36"; team_rank = 2; opp_rank = 5
        team_elo_rating = 1865; opp_elo_rating = 1805; team_win_pct = 0.67; opp_win_pct = 0.58
        team_game_win_pct = 0.63; opp_game_win_pct = 0.56; team_radiant_pct = 0.60; opp_radiant_pct = 0.54
        team_dire_pct = 0.58; opp_dire_pct = 0.52; team_laning = 88; opp_laning = 82
        team_mid = 87; opp_mid_game = 81; team_late = 89; opp_late = 84
        team_gd10 = 380; opp_gd10 = 150; team_gd20 = 1250; opp_gd20 = 560
        team_xpd10 = 240; opp_xpd10 = 100; team_xpd20 = 980; opp_xpd20 = 430
        team_first_blood_pct = 0.56; opp_first_blood_pct = 0.50; team_first_tower_pct = 0.58; opp_first_tower_pct = 0.51
        team_roshan_pct = 0.66; opp_roshan_pct = 0.56; team_tower_pressure = 88; opp_tower_pressure = 80
        team_objective_score = 88; opp_objective_score = 80; team_vision_score = 86; opp_vision_score = 79
        team_kills_per_game = 28.5; opp_kills_per_game = 25.2; team_deaths_per_game = 23.4; opp_deaths_per_game = 26.2
        team_kda_value = 4.4; opp_kda_value = 3.5; team_gpm_value = 2260; opp_gpm_value = 2160
        team_xpm_value = 2680; opp_xpm_value = 2520; team_networth = 88; opp_networth = 80
        team_draft_score = 89; opp_draft_score = 81; team_hero_pool = 9; opp_hero_pool = 7
        team_meta_fit = 88; opp_meta_fit = 80; carry_rating = 89; mid_rating = 91; offlane_rating = 87
        soft_support_rating = 86; hard_support_rating = 85; opp_carry_rating = 84; opp_mid_rating = 85
        opp_offlane_rating = 83; opp_soft_support_rating = 82; opp_hard_support_rating = 81
        roster_stability_score = 0.92; substitute = 0.02; availability_risk = 0.03; rest = 4; travel = 0.15
        lan = $true; online = $false; tier = "major"; playoff = $true; elimination = $false; form = 85; opp_form = 78
        market_move = 0.0; public_pct = 54; sharp_pct = 58
        player_name = "Nisha"; role = "mid"; hero_pool = 90; player_meta_fit = 88
        kills_proj = 8.4; assists_proj = 12.2; deaths_proj = 3.2; kda_proj = 6.4
        last_hits_proj = 320; gpm_proj = 625; xpm_proj = 710; net_worth_proj = 26500
        maps_proj = 2.4; prop_line = 7.5; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "dota2" -League "The International" -Event "Team Liquid vs Gaimin Gladiators" -Market "match_winner" -Selection "Team Liquid" -InputStats $stats
    $payload.visible_markets = @("match_winner", "first_roshan", "player_kills")
    return $payload
}

function New-CoDPayload {
    $stats = @{
        team_name = "Atlanta FaZe"; opponent_name = "OpTic Texas"; pick = "Atlanta FaZe"
        format = "bo5"; maps = 5; map = "Rio"; mode = "hardpoint"; rotation = "HP-SND-Control-HP-SND"
        team_rank = 1; opp_rank = 4; team_elo_rating = 1880; opp_elo_rating = 1815
        team_win_pct = 0.69; opp_win_pct = 0.59; team_map_pct = 0.65; opp_map_pct = 0.56
        team_hp_pct = 0.68; opp_hp_pct = 0.58; team_snd_pct = 0.62; opp_snd_pct = 0.54
        team_control_pct = 0.64; opp_control_pct = 0.55; team_respawn = 89; opp_respawn = 82
        team_snd = 86; opp_snd = 80; team_control = 87; opp_control = 81
        team_slaying = 90; opp_slaying = 84; team_objective = 88; opp_objective = 82
        team_breaking = 87; opp_breaking = 80; team_hold = 89; opp_hold = 83
        team_rotation = 90; opp_rotation = 82; team_first_blood_pct = 0.56; opp_first_blood_pct = 0.50
        team_clutch_pct = 0.55; opp_clutch_pct = 0.49; team_trade_pct = 0.63; opp_trade_pct = 0.57
        team_kd = 1.10; opp_kd = 1.02; team_damage_round = 485; opp_damage_round = 455
        team_map_depth = 7; opp_map_depth = 6; team_pick_pct = 0.36; opp_pick_pct = 0.30
        team_ban_pct = 0.12; opp_ban_pct = 0.17; lan = $true; online = $false
        tier = "major"; playoff = $true; elimination = $false; region = "NA"
        rest = 4; travel = 0.15; roster_stability_score = 0.92; substitute = 0.02
        availability_risk = 0.03; form = 86; opp_form = 79; market_move = 0.0
        public_pct = 54; sharp_pct = 58
        player_name = "Simp"; role = "SMG"; kills_proj = 24.5; assists_proj = 7.5
        deaths_proj = 20.5; kda_proj = 1.55; damage_proj = 3150; objective_time_proj = 72
        first_bloods_proj = 3.1; maps_proj = 4.2; prop_line = 23.5; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "cod" -League "CDL" -Event "Atlanta FaZe vs OpTic Texas" -Market "match_winner" -Selection "Atlanta FaZe" -InputStats $stats
    $payload.visible_markets = @("match_winner", "hardpoint_winner", "player_kills")
    return $payload
}

function New-OverwatchPayload {
    $stats = @{
        team_name = "San Francisco Shock"; opponent_name = "Dallas Fuel"; pick = "San Francisco Shock"
        format = "bo5"; maps = 5; map = "Lijiang Tower"; mode = "control"; rotation = "Control-Hybrid-Escort-Push-Control"; patch = "2.10"
        team_rank = 2; opp_rank = 6; team_elo_rating = 1860; opp_elo_rating = 1790
        team_win_pct = 0.67; opp_win_pct = 0.58; team_map_pct = 0.64; opp_map_pct = 0.55
        team_control_pct = 0.66; opp_control_pct = 0.57; team_escort_pct = 0.62; opp_escort_pct = 0.54
        team_hybrid_pct = 0.63; opp_hybrid_pct = 0.55; team_push_pct = 0.61; opp_push_pct = 0.53
        team_flashpoint_pct = 0.60; opp_flashpoint_pct = 0.52; team_clash_pct = 0.59; opp_clash_pct = 0.51
        team_fight_pct = 0.58; opp_fight_pct = 0.52; team_first_fight_pct = 0.56; opp_first_fight_pct = 0.50
        team_objective_score = 88; opp_objective_score = 81; team_ult_econ = 89; opp_ult_econ = 82
        team_ult_conversion = 0.64; opp_ult_conversion = 0.56; team_stagger = 87; opp_stagger = 80
        team_comp = 90; opp_comp = 82; team_meta_fit = 89; opp_meta_fit = 81
        team_tank = 88; opp_tank = 82; team_dps = 90; opp_dps = 84; team_support = 87; opp_support = 82
        team_damage10 = 8200; opp_damage10 = 7800; team_healing10 = 6900; opp_healing10 = 6500
        team_elims10 = 23.5; opp_elims10 = 21.0; team_deaths10 = 18.2; opp_deaths10 = 20.4
        team_final_blow_pct = 0.54; opp_final_blow_pct = 0.49; team_map_depth = 7; opp_map_depth = 6
        team_pick_pct = 0.34; opp_pick_pct = 0.28; team_ban_pct = 0.12; opp_ban_pct = 0.17
        lan = $true; online = $false; tier = "major"; playoff = $true; elimination = $false; region = "NA"
        rest = 4; travel = 0.14; roster_stability_score = 0.92; substitute = 0.02
        availability_risk = 0.03; form = 85; opp_form = 78; market_move = 0.0
        public_pct = 54; sharp_pct = 58
        player_name = "Proper"; role = "DPS"; hero_pool = 91; player_meta_fit = 89
        elims_proj = 29.5; final_blows_proj = 12.5; assists_proj = 10.5; deaths_proj = 8.5
        damage_proj = 11800; healing_proj = 500; mitigation_proj = 850; kda_proj = 4.6
        maps_proj = 4.2; prop_line = 28.5; book_count = 8
    }
    $payload = New-LiveTicketBase -Sport "overwatch" -League "OWCS" -Event "San Francisco Shock vs Dallas Fuel" -Market "match_winner" -Selection "San Francisco Shock" -InputStats $stats
    $payload.visible_markets = @("match_winner", "control_map_winner", "player_eliminations")
    return $payload
}

function New-LiveActivePayload {
    param([Parameter(Mandatory = $true)] [string] $Sport)
    switch ($Sport.ToLower()) {
        "nba" { return New-NbaPayload }
        "nfl" { return New-NflPayload }
        "mlb" { return New-MlbPayload }
        "soccer" { return New-SoccerPayload }
        "rugby" { return New-RugbyPayload }
        "rugby_union" { return New-RugbyPayload }
        "rugby_league" { return New-RugbyPayload }
        "nrl" { return New-RugbyPayload }
        "super_rugby" { return New-RugbyPayload }
        "six_nations" { return New-RugbyPayload }
        "premiership_rugby" { return New-RugbyPayload }
        "united_rugby_championship" { return New-RugbyPayload }
        "rugby_world_cup" { return New-RugbyPayload }
        "top_14" { return New-RugbyPayload }
        "lacrosse" { return New-LacrossePayload }
        "table_tennis" { return New-TableTennisPayload }
        "ping_pong" { return New-TableTennisPayload }
        "pingpong" { return New-TableTennisPayload }
        "ittf" { return New-TableTennisPayload }
        "wtt" { return New-TableTennisPayload }
        "world_table_tennis" { return New-TableTennisPayload }
        "olympic_table_tennis" { return New-TableTennisPayload }
        "badminton" { return New-BadmintonPayload }
        "bwf" { return New-BadmintonPayload }
        "world_badminton" { return New-BadmintonPayload }
        "olympic_badminton" { return New-BadmintonPayload }
        "badminton_singles" { return New-BadmintonPayload }
        "badminton_doubles" { return New-BadmintonPayload }
        "bwf_world_tour" { return New-BadmintonPayload }
        "pickleball" { return New-PickleballPayload }
        "pro_pickleball" { return New-PickleballPayload }
        "ppa" { return New-PickleballPayload }
        "mlf" { return New-PickleballPayload }
        "major_league_pickleball" { return New-PickleballPayload }
        "app_tour" { return New-PickleballPayload }
        "pickleball_singles" { return New-PickleballPayload }
        "pickleball_doubles" { return New-PickleballPayload }
        "volleyball" { return New-VolleyballPayload }
        "indoor_volleyball" { return New-VolleyballPayload }
        "beach_volleyball" { return New-VolleyballPayload }
        "ncaa_volleyball" { return New-VolleyballPayload }
        "mens_volleyball" { return New-VolleyballPayload }
        "womens_volleyball" { return New-VolleyballPayload }
        "fivb" { return New-VolleyballPayload }
        "vnl" { return New-VolleyballPayload }
        "avp" { return New-VolleyballPayload }
        "olympic_volleyball" { return New-VolleyballPayload }
        "handball" { return New-HandballPayload }
        "team_handball" { return New-HandballPayload }
        "european_handball" { return New-HandballPayload }
        "olympic_handball" { return New-HandballPayload }
        "ehf" { return New-HandballPayload }
        "ihf" { return New-HandballPayload }
        "handball_bundesliga" { return New-HandballPayload }
        "champions_league_handball" { return New-HandballPayload }
        "water_polo" { return New-WaterPoloPayload }
        "waterpolo" { return New-WaterPoloPayload }
        "olympic_water_polo" { return New-WaterPoloPayload }
        "ncaa_water_polo" { return New-WaterPoloPayload }
        "world_aquatics_water_polo" { return New-WaterPoloPayload }
        "fina_water_polo" { return New-WaterPoloPayload }
        "mens_water_polo" { return New-WaterPoloPayload }
        "womens_water_polo" { return New-WaterPoloPayload }
        "lax" { return New-LacrossePayload }
        "mens_lacrosse" { return New-LacrossePayload }
        "womens_lacrosse" { return New-LacrossePayload }
        "college_lacrosse" { return New-LacrossePayload }
        "ncaa_lacrosse" { return New-LacrossePayload }
        "pll" { return New-LacrossePayload }
        "premier_lacrosse_league" { return New-LacrossePayload }
        "nll" { return New-LacrossePayload }
        "national_lacrosse_league" { return New-LacrossePayload }
        "afl" { return New-AFLPayload }
        "australian_rules" { return New-AFLPayload }
        "aussie_rules" { return New-AFLPayload }
        "australian_football" { return New-AFLPayload }
        "australian_rules_football" { return New-AFLPayload }
        "afl_football" { return New-AFLPayload }
        "australian_football_league" { return New-AFLPayload }
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
        "formula_e" { return New-FormulaEPayload }
        "formulae" { return New-FormulaEPayload }
        "fe" { return New-FormulaEPayload }
        "fia_formula_e" { return New-FormulaEPayload }
        "abb_formula_e" { return New-FormulaEPayload }
        "electric_racing" { return New-FormulaEPayload }
        "motorsport_formula_e" { return New-FormulaEPayload }
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
        "dota2" { return New-Dota2Payload }
        "dota_2" { return New-Dota2Payload }
        "dota" { return New-Dota2Payload }
        "esports_dota2" { return New-Dota2Payload }
        "dota_pro_circuit" { return New-Dota2Payload }
        "dpc" { return New-Dota2Payload }
        "the_international" { return New-Dota2Payload }
        "ti" { return New-Dota2Payload }
        "call_of_duty" { return New-CoDPayload }
        "cod" { return New-CoDPayload }
        "cdl" { return New-CoDPayload }
        "esports_cod" { return New-CoDPayload }
        "cod_league" { return New-CoDPayload }
        "callofduty" { return New-CoDPayload }
        "call_of_duty_league" { return New-CoDPayload }
        "overwatch" { return New-OverwatchPayload }
        "overwatch2" { return New-OverwatchPayload }
        "overwatch_2" { return New-OverwatchPayload }
        "ow" { return New-OverwatchPayload }
        "ow2" { return New-OverwatchPayload }
        "esports_overwatch" { return New-OverwatchPayload }
        "overwatch_league" { return New-OverwatchPayload }
        "owl" { return New-OverwatchPayload }
        "overwatch_champions_series" { return New-OverwatchPayload }
        "owcs" { return New-OverwatchPayload }
        default { throw "No live active payload builder registered for sport '$Sport'." }
    }
}
