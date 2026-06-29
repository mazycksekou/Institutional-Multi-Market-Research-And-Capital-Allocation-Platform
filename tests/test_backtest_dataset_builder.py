import json

from src.services.streamlit_dashboard_facade import build_canonical_backtest_dataset, discover_backtest_artifacts, extract_backtest_rows_from_artifact, load_canonical_backtest_dataset, summarize_canonical_dataset_report


def test_extract_backtest_rows_from_artifact_normalizes_nested_rows(tmp_path):
    artifact = tmp_path / "artifact.json"
    artifact.write_text(
        json.dumps(
            {
                "paper_decisions": [
                    {
                        "event": "e1",
                        "market_type": "moneyline",
                        "odds": 100,
                        "predicted_probability": 0.57,
                        "ev_percent": 3.0,
                        "features": {"pace": 99.1},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    extracted = extract_backtest_rows_from_artifact(artifact)

    assert extracted["row_count"] == 1
    row = extracted["rows"][0]
    assert row["event_id"] == "e1"
    assert row["recommended_odds"] == 100
    assert row["model_probability"] == 0.57
    assert row["_source_row_path"] == "root.paper_decisions"


def test_build_canonical_backtest_dataset_writes_jsonl_and_schema_report(tmp_path):
    artifact = tmp_path / "paper.json"
    output = tmp_path / "latest.jsonl"
    schema = tmp_path / "schema_report.json"

    artifact.write_text(
        json.dumps(
            [
                {
                    "event": "e1",
                    "market_type": "moneyline",
                    "odds": 100,
                    "predicted_probability": 0.57,
                    "ev_percent": 3.0,
                    "result_status": "win",
                    "closing_odds": -110,
                    "features": {"pace": 99.1},
                },
                {
                    "event": "e2",
                    "market_type": "spread",
                    "odds": -110,
                    "predicted_probability": 0.54,
                    "ev_percent": 2.0,
                    "features": {"pace": 96.1},
                },
            ]
        ),
        encoding="utf-8",
    )

    report = build_canonical_backtest_dataset(
        artifact_paths=[artifact],
        output_jsonl_path=output,
        schema_report_path=schema,
    )

    rows = load_canonical_backtest_dataset(output)

    assert report["rows_written"] == 2
    assert output.exists()
    assert schema.exists()
    assert rows[0]["event_id"] == "e1"
    assert rows[0]["model_probability"] == 0.57
    assert report["leakage_summary"]["ok"] is True


def test_build_canonical_backtest_dataset_can_drop_core_incomplete_rows(tmp_path):
    artifact = tmp_path / "paper.json"
    output = tmp_path / "latest.jsonl"
    schema = tmp_path / "schema_report.json"

    artifact.write_text(
        json.dumps(
            [
                {"event": "e1", "market_type": "moneyline", "odds": 100, "predicted_probability": 0.57},
                {"event": "e2"},
            ]
        ),
        encoding="utf-8",
    )

    report = build_canonical_backtest_dataset(
        artifact_paths=[artifact],
        output_jsonl_path=output,
        schema_report_path=schema,
        require_core_fields=True,
    )

    rows = load_canonical_backtest_dataset(output)

    assert report["rows_written"] == 1
    assert report["rows_dropped"] == 1
    assert rows[0]["event_id"] == "e1"


def test_discover_backtest_artifacts_finds_default_data_files(tmp_path):
    target = tmp_path / "data" / "paper_ledger"
    target.mkdir(parents=True)
    artifact = target / "latest.json"
    artifact.write_text("[]", encoding="utf-8")

    found = discover_backtest_artifacts(base_dir=tmp_path)

    assert artifact in found


def test_summarize_canonical_dataset_report_is_compact(tmp_path):
    artifact = tmp_path / "paper.json"
    output = tmp_path / "latest.jsonl"
    schema = tmp_path / "schema_report.json"
    artifact.write_text(json.dumps([{"event": "e1", "odds": 100, "predicted_probability": 0.57}]), encoding="utf-8")

    report = build_canonical_backtest_dataset(
        artifact_paths=[artifact],
        output_jsonl_path=output,
        schema_report_path=schema,
    )
    summary = summarize_canonical_dataset_report(report)

    assert summary["rows_written"] == 1
    assert "schema" not in summary
    assert summary["output_jsonl_path"] == str(output)
