from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "reports" / "NFL_FEATURE_REGISTRY.md"
DEPENDENCY_PATH = ROOT / "docs" / "reports" / "NFL_FEATURE_DEPENDENCY_GRAPH.md"


def _markdown_table(path: Path, heading: str) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = lines.index(heading)
    table_lines = [line for line in lines[start + 1 :] if line.startswith("|")]
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        values = [cell.strip() for cell in line.strip("|").split("|")]
        if len(values) != len(headers):
            continue
        rows.append(dict(zip(headers, values)))
    return rows


def test_nfl_feature_registry_required_fields_are_populated() -> None:
    rows = _markdown_table(REGISTRY_PATH, "## Canonical Registry")
    required_columns = {
        "Feature ID",
        "Feature Name",
        "Feature Family",
        "Feature Category",
        "Owner",
        "Profile Family",
        "Storage Destination",
        "Research Usage",
        "Validation Usage",
        "Leakage Classification",
        "Readiness Status",
    }

    assert len(rows) >= 35
    assert required_columns.issubset(rows[0])

    for row in rows:
        for column in required_columns:
            assert row[column], f"{row['Feature ID']} missing {column}"
        assert row["Profile Family"] == "sports:nfl"
        assert row["Leakage Classification"] in {
            "POINT_IN_TIME_SAFE",
            "CUTOFF_REQUIRED",
            "LEAKAGE_RISK",
            "RESULT_ONLY",
            "POST_EVENT_ONLY",
            "DEFERRED_UNKNOWN",
        }
        assert row["Readiness Status"] in {
            "Ready",
            "Needs Provider",
            "Needs Calculation",
            "Needs Validation",
            "Needs Research",
            "Deferred",
            "Blocked",
        }


def test_nfl_feature_registry_ids_are_unique() -> None:
    rows = _markdown_table(REGISTRY_PATH, "## Canonical Registry")
    feature_ids = [row["Feature ID"] for row in rows]

    assert len(feature_ids) == len(set(feature_ids))


def test_composite_features_have_dependency_documentation() -> None:
    rows = _markdown_table(REGISTRY_PATH, "## Canonical Registry")
    dependency_text = DEPENDENCY_PATH.read_text(encoding="utf-8")
    composite_ids = [
        row["Feature ID"]
        for row in rows
        if row["Atomic/Composite"] == "Composite" and row["Readiness Status"] != "Deferred"
    ]

    missing = [feature_id for feature_id in composite_ids if feature_id not in dependency_text]
    assert not missing, f"composite features missing dependency rows: {missing}"


def test_registry_remains_documentation_only() -> None:
    text = REGISTRY_PATH.read_text(encoding="utf-8").lower()

    assert "does not implement providers" in text
    assert "does not implement" in text
    assert "provider calls" not in text

