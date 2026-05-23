$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"

Invoke-LiveSportSmoke -Sport "motogp" -ExpectedModel "motogp_rider_bike_tire_weather_monte_carlo_model" -ExpectedCalibration "motogp"
