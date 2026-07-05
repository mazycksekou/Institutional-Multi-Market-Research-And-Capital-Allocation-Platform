from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PATH = ROOT / "data" / "outcomes" / "migration" / "kalshi_local_outcomes_migration.latest.json"


def _load_package() -> dict[str, object]:
    if not PACKAGE_PATH.exists():
        raise FileNotFoundError(f"Migration package not found: {PACKAGE_PATH}. Run scripts/export_kalshi_local_outcomes.py first.")
    return json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))


def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    req = request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=60) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Send a dry-run Kalshi local outcomes import to the API.")
    parser.add_argument("--base-url", default=None, help="Base URL of the deployment, e.g. https://example.onrender.com.")
    args = parser.parse_args(argv)

    if not args.base_url:
        raise SystemExit("APP_BASE_URL or --base-url is required for dry-run import.")

    package = _load_package()
    payload = {
        "dry_run": True,
        "persist": False,
        "source": "local_repo_migration",
        "migration_version": package["migration_version"],
        "records": package["records"],
        "supporting_paper_decisions": package["supporting_paper_decisions"],
    }
    url = f"{args.base_url.rstrip('/')}/api/automation/outcomes/import-local-settlements"
    try:
        response = _post_json(url, payload)
    except (OSError, error.URLError, error.HTTPError) as exc:
        raise SystemExit(f"Dry-run import failed: {exc}") from exc
    print(json.dumps(response, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
