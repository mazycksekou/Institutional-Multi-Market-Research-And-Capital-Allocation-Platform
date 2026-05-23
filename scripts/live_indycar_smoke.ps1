$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"

Invoke-LiveSportSmoke -Sport "indycar" -ExpectedModel "indycar_aero_strategy_restart_pit_variance_monte_carlo_model" -ExpectedCalibration "indycar"
