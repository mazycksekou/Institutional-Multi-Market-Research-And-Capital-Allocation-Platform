# API Layer Thinning Sequence After 10K8ZHE

1. Keep `src/api/system_routes.py`, `quant_routes.py`, `market_metadata_routes.py`, and `market_utility_routes.py` as thin API shells.
2. Leave `src/api/model_card_service.py` as the API-facing service object that wraps canonical provider routing.
3. Redirect `src/api/provider_status_routes.py` away from `automation_scheduler` only after a canonical replacement is proven.
4. Move automation route dependencies into `src.services` only when a safe service replacement exists.
5. Keep API exposure thin; do not move math, pricing, or provider ownership into routes.
