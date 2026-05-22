$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"

Invoke-LiveSportSmoke -Sport "nascar" -ExpectedModel "nascar_track_position_speed_rating_pit_variance_monte_carlo_model" -ExpectedCalibration "nascar"
