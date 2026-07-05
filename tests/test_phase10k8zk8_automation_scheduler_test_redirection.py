from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase10k8zk8_test_redirection_docs_exist() -> None:
    docs = [
        ROOT / 'PHASE10K8ZK8_AUTOMATION_SCHEDULER_TEST_REDIRECTION.md',
        ROOT / 'AUTOMATION_SCHEDULER_TEST_REFERENCE_SCAN_AFTER_10K8ZK8.md',
        ROOT / 'AUTOMATION_SCHEDULER_TEST_REDIRECTION_MAP_AFTER_10K8ZK8.md',
        ROOT / 'AUTOMATION_SCHEDULER_TEST_DELETE_READINESS_AFTER_10K8ZK8.md',
    ]
    for path in docs:
        assert path.is_file(), path
    text = '\n'.join(path.read_text(encoding='utf-8') for path in docs)
    assert 'Historical test references are documented separately from runtime dependencies.' in text
    assert 'Test callers remain historically large' in text or 'test callers' in text
    assert 'Delete-ready files are not preserved by tests' in text
