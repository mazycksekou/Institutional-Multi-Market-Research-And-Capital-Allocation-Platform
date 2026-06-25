from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase10k8zk7_runtime_redirection_docs_exist() -> None:
    docs = [
        ROOT / 'PHASE10K8ZK7_AUTOMATION_SCHEDULER_RUNTIME_REDIRECTION.md',
        ROOT / 'AUTOMATION_SCHEDULER_RUNTIME_IMPORTS_AFTER_10K8ZK7.md',
        ROOT / 'AUTOMATION_SCHEDULER_RUNTIME_REDIRECTION_MAP_AFTER_10K8ZK7.md',
        ROOT / 'AUTOMATION_SCHEDULER_RUNTIME_DELETE_READINESS_AFTER_10K8ZK7.md',
    ]
    for path in docs:
        assert path.is_file(), path
    text = '\n'.join(path.read_text(encoding='utf-8') for path in docs)
    assert 'Runtime callers are explicitly justified' in text
    assert 'main.py' in text or 'streamlit_app.py' in text
    assert 'src.api' in text or 'src.services' in text
    assert 'No delete-ready file appears in the runtime reference set' in text
