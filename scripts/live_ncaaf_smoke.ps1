$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"
Invoke-LiveSportSmoke -Sport "ncaaf" -ExpectedModel "college_football_epa_drive_rating_monte_carlo_model" -ExpectedCalibration "ncaaf"

