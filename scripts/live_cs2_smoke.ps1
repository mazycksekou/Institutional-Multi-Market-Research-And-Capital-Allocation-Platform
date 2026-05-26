$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"
Invoke-LiveSportSmoke -Sport "cs2" -ExpectedModel "cs2_round_economy_map_pool_monte_carlo_model" -ExpectedCalibration "cs2"
