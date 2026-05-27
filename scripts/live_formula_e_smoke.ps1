$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_payloads.ps1"
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "formula_e" -ExpectedModel "formula_e_energy_management_attack_mode_street_circuit_monte_carlo_model" -ExpectedCalibration "formula_e"
