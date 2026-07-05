# Post Service Thinning Architecture Map After 10K8ZHH

```mermaid
flowchart LR
    UI["streamlit_app.py"] --> SVC["src.services"]
    BOOT["main.py"] --> API["src.api"]
    API --> SVC
    SVC --> CORE["src.core"]
    SVC --> PROV["src.providers"]
    SVC --> CONN["src.connectors"]
    SCHED["automation_scheduler"] --> SVC
    SCHED --> DASH["automation_scheduler/streamlit_dashboard_data.py"]
```

## Notes

- `src.services` is the orchestration boundary.
- `src.core` is the math/risk/pricing/probability boundary.
- `src.providers` is the normalized provider boundary.
- `src.connectors` is the disabled raw data boundary.
- `main.py` and `streamlit_app.py` remain shell boundaries.
- `automation_scheduler` remains a decommission target.
