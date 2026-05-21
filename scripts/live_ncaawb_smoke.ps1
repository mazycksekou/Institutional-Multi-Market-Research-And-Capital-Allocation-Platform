$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"
Invoke-LiveSportSmoke -Sport "ncaawb" -ExpectedModel "womens_college_basketball_possession_variance_model" -ExpectedCalibration "ncaawb"

