from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "PHASE10K8ZFP_PROVIDER_TAXONOMY_CORRECTION.md"
PROVIDER_ROOT = ROOT / "src" / "providers"


def test_taxonomy_correction_doc_exists_and_states_vendor_neutral_policy():
    text = DOC_PATH.read_text(encoding="utf-8")
    assert "Executive Summary" in text
    assert "Reason for Correction" in text
    assert "Correct Canonical Provider Taxonomy" in text
    assert "Removed Vendor-Specific Skeleton Paths" in text
    assert "Added Product-Category Paths" in text
    assert "Vendor-Neutral Naming Policy" in text
    assert "What Was Not Changed" in text
    assert "Runtime Safety Statement" in text
    assert "Test Summary" in text
    assert "Next Recommended Phase" in text
    assert "Canonical provider ownership is product-category based, not vendor-name based. Prediction markets, 0DTE/stocks, and sportsbooks are the canonical provider categories. Vendor names such as Kalshi or Sharp must not define future package ownership." in text


def test_vendor_neutral_canonical_paths_exist_and_vendor_paths_do_not():
    assert (PROVIDER_ROOT / "prediction_markets").is_dir()
    assert (PROVIDER_ROOT / "zero_dte_stocks").is_dir()
    assert (PROVIDER_ROOT / "sportsbooks").is_dir()
    assert not (PROVIDER_ROOT / "kalshi").exists()

    lowered_paths = []
    for path in PROVIDER_ROOT.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        lowered_paths.append("/".join(part.lower() for part in path.parts))

    assert all("kalshi" not in path for path in lowered_paths)
    assert all("sharp" not in path for path in lowered_paths)
