$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

. "$ScriptDir\live_payloads.ps1"

$payloads = [ordered]@{}
foreach ($sport in @("nba","nfl","mlb","soccer","nhl","tennis","combat","golf","wnba","ncaab","ncaawb","ncaaf","f1","nascar","indycar","motogp","cricket","cs2","valorant","lol","dota2","cod")) {
    $payloads[$sport] = New-LiveActivePayload -Sport $sport
}

$tempPayloads = Join-Path $env:TEMP ("live_payload_contract_" + [guid]::NewGuid().ToString() + ".json")
$payloads | ConvertTo-Json -Depth 80 | Set-Content -LiteralPath $tempPayloads -Encoding UTF8

$python = (Get-Command python -ErrorAction SilentlyContinue)
if ($python) {
    $pythonExe = $python.Source
} else {
    $bundled = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) {
        $pythonExe = $bundled
    } else {
        Write-Host "Python runtime not found."
        exit 1
    }
}

$pythonCode = @'
import json
import pathlib
import sys

repo_root = pathlib.Path(sys.argv[1])
payload_path = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "venv" / "Lib" / "site-packages"))

import multi_sport_model_registry as registry

payloads = json.loads(payload_path.read_text(encoding="utf-8-sig"))
failed = False

def analysis_payload(ticket):
    return {
        "sport": ticket.get("sport"),
        "league": ticket.get("league"),
        "event_id": ticket.get("event") or ticket.get("event_id"),
        "market": ticket.get("market"),
        "selection": ticket.get("selection"),
        "odds_american": ticket.get("odds_american"),
        "line": ticket.get("line") if ticket.get("line") is not None else ticket.get("total_line"),
        "bankroll": ticket.get("bankroll"),
        "unit_size": ticket.get("unit_size"),
        "risk_profile": ticket.get("risk_profile"),
        "input_stats": ticket.get("input_stats") or {},
    }

for name, payload in payloads.items():
    normalized = registry.normalize_sport_inputs_for_model(
        sport=payload.get("sport"),
        market=payload.get("market"),
        selection=payload.get("selection"),
        input_stats=payload.get("input_stats"),
        ticket=payload,
    )
    response = registry.analyze_sport_model(analysis_payload(payload))
    missing = normalized.get("missing_inputs_after_normalization") or []
    complete = not missing and response.get("model_status") == "active" and response.get("final_probability") is not None
    failed = failed or not complete
    print(f"SPORT: {response.get('sport') or payload.get('sport')}")
    print(f"MODEL: {response.get('model_name') or ''}")
    print(f"ACTIVE_PAYLOAD_COMPLETE: {complete}")
    print("MISSING_INPUTS:")
    if missing:
        for field in missing:
            print(f"- {field}")
    else:
        print("- none")
    print(f"NORMALIZER_USED: {normalized.get('normalizer_used')}")
    print(f"PASS: {complete}")
    print("----------------------------------------")

sys.exit(1 if failed else 0)
'@

$tempScript = Join-Path $env:TEMP ("live_payload_contract_" + [guid]::NewGuid().ToString() + ".py")
$pythonCode | Set-Content -LiteralPath $tempScript -Encoding UTF8
try {
    & $pythonExe $tempScript $RepoRoot $tempPayloads
    exit $LASTEXITCODE
} finally {
    Remove-Item -LiteralPath $tempPayloads -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $tempScript -ErrorAction SilentlyContinue
}
