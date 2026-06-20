# PROVIDER_ROUTER_SPLIT_PLAN_AFTER_10K8ZFW

## Router Split Plan

## Executive Summary
The router split now has a canonical product-category classification layer in `src.providers.routing`. Legacy routers still handle live adapter instantiation and compatibility defaults, but the category decision is now centralized and product-category based.

## Canonical Routing Model
- `prediction_markets`
- `sportsbooks`
- `zero_dte_stocks`

## Canonical Routing Helpers
- `src.providers.categories.normalize_provider_category`
- `src.providers.categories.provider_category_from_provider_type`
- `src.providers.routing.provider_category_from_provider_id`
- `src.providers.routing.resolve_provider_category`
- `src.providers.routing.provider_route_package`
- `src.providers.routing.category_route_summary`

## Legacy Router Split
- `betting_providers.provider_router` remains the live compatibility router
- Legacy default provider selection remains until later migration batches
- Legacy vendor routing is now compatibility detail, not canonical ownership

## Deferred Areas
- `main.py`
- `streamlit_app.py`
- API route rewrites
- live adapter migration
- connector migration

## Next Step
Later batches can redirect router call sites to the canonical category helpers and then shrink the legacy router to a compatibility shell.
