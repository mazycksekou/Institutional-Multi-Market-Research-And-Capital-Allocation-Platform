$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_payloads.ps1"
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "dota2" -ExpectedModel "dota2_draft_lane_objective_roshan_monte_carlo_model" -ExpectedCalibration "dota2"
