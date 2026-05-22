$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"
Invoke-LiveSportSmoke -Sport "f1" -ExpectedModel "f1_qualifying_race_pace_pit_strategy_monte_carlo_model" -ExpectedCalibration "f1"
