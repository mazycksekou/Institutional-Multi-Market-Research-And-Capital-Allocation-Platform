$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"
Invoke-LiveSportSmoke -Sport "cricket" -ExpectedModel "cricket_run_rate_wicket_resource_monte_carlo_model" -ExpectedCalibration "cricket"
