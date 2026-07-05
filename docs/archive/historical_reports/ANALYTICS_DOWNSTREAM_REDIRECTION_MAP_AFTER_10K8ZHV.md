# Analytics Downstream Redirection Map After 10K8ZHV

| Legacy file | New canonical owner | Wrapper status | Deletion status |
| --- | --- | --- | --- |
| `model_governance/governance_health.py` | `src.analytics.governance.build_governance_health` | Compatibility wrapper | Delete candidate after import/test proof |
| `model_governance/governance_report.py` | `src.analytics.reports.generate_governance_report` | Compatibility wrapper | Delete candidate after proof |
| `model_governance/model_validation_report.py` | `src.analytics.reports.build_model_validation_report` | Compatibility wrapper | Delete candidate after proof |

## Notes
- The canonical health helper now owns summary construction.
- The legacy modules remain importable for compatibility.
- No legacy analytics file was deleted in this batch.
