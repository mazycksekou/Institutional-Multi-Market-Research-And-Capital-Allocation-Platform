from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOCS = {
    "roadmap": ROOT / "LEGACY_VENDOR_TRANSPORT_ROADMAP_AFTER_10K8ZFS.md",
    "matrix": ROOT / "LEGACY_VENDOR_DESTINATION_MATRIX_AFTER_10K8ZFS.md",
    "batch": ROOT / "FIRST_SAFE_TRANSPORT_BATCH_AFTER_10K8ZFS.md",
    "queue": ROOT / "LEGACY_DELETE_AND_SHIM_QUEUE_AFTER_10K8ZFS.md",
    "exit": ROOT / "AUTOMATION_SCHEDULER_EXIT_SEQUENCE_AFTER_10K8ZFS.md",
    "plan": ROOT / "PHASE10K8ZFS_LEGACY_VENDOR_TRANSPORT_BATCH_PLAN.md",
}


def test_legacy_vendor_transport_batch_plan_docs_exist_and_cover_required_phrases():
    for doc in DOCS.values():
        assert doc.is_file()

    roadmap = DOCS["roadmap"].read_text(encoding="utf-8")
    assert "Executive Summary" in roadmap
    assert "Current Domain Boundaries" in roadmap
    assert "Migration Principles" in roadmap
    assert "Ordered Migration Batches" in roadmap
    assert "Batch 1 Recommended Scope" in roadmap
    assert "Batch 2 Recommended Scope" in roadmap
    assert "Batch 3 Recommended Scope" in roadmap
    assert "Deletion Policy" in roadmap
    assert "Shim Policy" in roadmap
    assert "Test Rewrite Policy" in roadmap
    assert "Rollback Strategy" in roadmap
    assert "Next Recommended Phase" in roadmap

    matrix = DOCS["matrix"].read_text(encoding="utf-8")
    assert "Destination Matrix" in matrix
    assert "src/providers/prediction_markets" in matrix
    assert "src/providers/sportsbooks" in matrix
    assert "src/connectors/prediction_market_data" in matrix
    assert "src/connectors/odds_data" in matrix
    assert "src/ai/policy" in matrix
    assert "src/brokerage/execution" in matrix
    assert "src/core" in matrix
    assert "compatibility-only" in matrix

    batch = DOCS["batch"].read_text(encoding="utf-8")
    assert "First Safe Transport Batch" in batch or "FIRST_SAFE_TRANSPORT_BATCH" in batch
    assert "Exact Files / Modules To Migrate Later" in batch
    assert "Exact Destination" in batch
    assert "No-Network Guarantee" in batch
    assert "No-Credential Guarantee" in batch
    assert "Rollback Plan" in batch
    assert "Expected Deletion Candidates After Successful Migration" in batch

    queue = DOCS["queue"].read_text(encoding="utf-8")
    assert "Temporary Shim Candidates" in queue
    assert "Delete After Migration" in queue
    assert "Delete Only After Tests Are Rewritten" in queue
    assert "Not To Be Deleted Yet" in queue
    assert "Non-Goal But Still Need Proof Before Deletion" in queue
    assert "Legacy Vendor Docs To Rewrite" in queue
    assert "Legacy Vendor Tests To Rename Or Generalize" in queue

    exit_text = DOCS["exit"].read_text(encoding="utf-8")
    assert "What Must Leave automation_scheduler First" in exit_text
    assert "What Must Leave automation_scheduler Later" in exit_text
    assert "What AI / Brokerage / Scraper References Must Be Isolated Outside automation_scheduler" in exit_text
    assert "What Can Become a Compatibility Shim" in exit_text
    assert "What Must Be Proven Before automation_scheduler Can Shrink" in exit_text
    assert "Proposed Exit Sequence" in exit_text
    assert "automation_scheduler should eventually become orchestration-only" in exit_text.lower() or "shrink" in exit_text.lower()

    plan = DOCS["plan"].read_text(encoding="utf-8")
    assert "Summary" in plan
    assert "Files Reviewed" in plan
    assert "What Was Decided" in plan
    assert "What Was Not Changed" in plan
    assert "Current Safety Posture" in plan
    assert "Next Recommended Phase" in plan
    assert "Useful legacy vendor functionality should be transported into the correct production domain." in plan

    combined = "\n".join(doc.read_text(encoding="utf-8") for doc in DOCS.values())
    assert "AKIA" not in combined
    assert "ASIA" not in combined
    assert "your_real_secret" not in combined
