$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_payloads.ps1"
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "cod" -ExpectedModel "call_of_duty_map_mode_rotation_respawn_snd_monte_carlo_model" -ExpectedCalibration "call_of_duty"
