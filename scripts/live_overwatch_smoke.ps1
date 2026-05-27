$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_payloads.ps1"
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "overwatch" -ExpectedModel "overwatch_hero_composition_map_mode_objective_monte_carlo_model" -ExpectedCalibration "overwatch"
