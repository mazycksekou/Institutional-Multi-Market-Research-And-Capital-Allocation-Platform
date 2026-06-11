from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from fastapi.responses import JSONResponse


def register_market_utility_routes(
    app: Any,
    *,
    provider_router: Any,
    model_card_service: Any,
    repo_root: Path,
) -> None:
    """
    Register odds, math, opportunity, and live model-card utility routes.

    Canonical owner: src/api/market_utility_routes.py
    """
    PROVIDER_ROUTER = provider_router
    MODEL_CARD_SERVICE = model_card_service

    @app.get("/odds/live")
    async def odds_live(limit: int = 10):
        payload = await PROVIDER_ROUTER.get_active_events("sportsgameodds", None, None, limit=limit)
        if not payload.get("ok"):
            status_code = int(payload.get("status_code") or 500)
            error = (
                "SPORTSGAMEODDS_API_KEY is missing"
                if payload.get("error_type") == "PROVIDER_NOT_CONFIGURED"
                else str(payload.get("message") or "SportsGameOdds provider request failed.")
            )
            return JSONResponse(
                status_code=status_code,
                content={"ok": False, "provider": "SportsGameOdds", "status_code": status_code, "error": error},
            )
        return {
            "ok": True,
            "source": "SportsGameOdds",
            "endpoint": "/odds/live",
            "limit": limit,
            "data": payload.get("raw_response", payload.get("events", [])),
        }

    @app.get("/odds/the-odds-api/live")
    async def the_odds_api_live(
        sport: str = "basketball_nba",
        regions: str = "us",
        markets: str = "h2h,spreads,totals",
        odds_format: str = "american",
    ):
        payload = await PROVIDER_ROUTER.get_odds_events(
            "the_odds_api",
            sport,
            None,
            regions=regions,
            markets=markets,
            odds_format=odds_format,
        )
        if not payload.get("ok"):
            status_code = int(payload.get("status_code") or 500)
            error = (
                "THE_ODDS_API_KEY is missing"
                if payload.get("error_type") == "PROVIDER_NOT_CONFIGURED"
                else str(payload.get("message") or "The Odds API provider request failed.")
            )
            return JSONResponse(
                status_code=status_code,
                content={"ok": False, "provider": "The Odds API", "status_code": status_code, "error": error},
            )
        return {
            "ok": True,
            "source": "The Odds API",
            "sport": sport,
            "regions": regions,
            "markets": markets,
            "odds_format": odds_format,
            "data": payload.get("raw_response", payload.get("events", [])),
        }

    @app.get("/odds/the-odds-api/test")
    async def the_odds_api_test():
        payload = await PROVIDER_ROUTER.get_supported_sports("the_odds_api")
        if not payload.get("ok"):
            status_code = int(payload.get("status_code") or 500)
            error = (
                "THE_ODDS_API_KEY is missing"
                if payload.get("error_type") == "PROVIDER_NOT_CONFIGURED"
                else str(payload.get("message") or "The Odds API provider request failed.")
            )
            return JSONResponse(
                status_code=status_code,
                content={"ok": False, "provider": "The Odds API", "status_code": status_code, "error": error},
            )
        sports = payload.get("sports") if isinstance(payload.get("sports"), list) else []
        headers = payload.get("response_headers") if isinstance(payload.get("response_headers"), dict) else {}
        return {
            "ok": True,
            "source": "The Odds API",
            "requests_remaining": headers.get("x-requests-remaining"),
            "requests_used": headers.get("x-requests-used"),
            "sports_count": len(sports),
            "sample": sports[:5],
        }

    @app.get("/math/catalog")
    def math_catalog(
        sport: str = "basketball_nba",
        include_all: bool = False,
        max_files: int = 120,
    ):
        root = repo_root

        exclude_dirs = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            ".cursor",
            ".uv-cache-checks",
            ".uv-python-checks",
            "data",
            "reports",
        }

        priority_files = {
            "model_probability.py",
            "quant_engine.py",
            "market_pricing.py",
            "bet_decision_engine.py",
            "risk_engine.py",
            "full_board_engine.py",
            "multi_sport_model_registry.py",
            "model_blender.py",
            "sharp_client.py",
            "kalshi_client.py",
            "logbook_engine.py",
        }

        priority_dirs = {
            "math_models",
            "providers",
            "betting_providers",
            "live_market_intelligence",
            "research_engine",
            "model_governance",
        }

        sport_keywords = {
            "basketball_nba": [
                "nba",
                "basketball",
                "possession",
                "pace",
                "offensive_rating",
                "defensive_rating",
                "efg",
                "turnover",
                "rebound",
                "free_throw",
                "usage",
                "minutes",
                "shot_quality",
                "fatigue",
                "four factors",
            ],
            "basketball_wnba": [
                "wnba",
                "basketball",
                "possession",
                "pace",
                "usage",
                "minutes",
                "shot_quality",
                "fatigue",
                "four factors",
            ],
            "baseball_mlb": [
                "mlb",
                "baseball",
                "pitcher",
                "batter",
                "runs",
                "strikeout",
                "walk",
                "barrel",
                "hard_hit",
                "park",
                "weather",
                "poisson",
            ],
            "americanfootball_nfl": [
                "nfl",
                "football",
                "spread",
                "yards",
                "epa",
                "success_rate",
                "pace",
                "trench",
                "pressure",
                "rush",
                "pass",
            ],
            "icehockey_nhl": [
                "nhl",
                "hockey",
                "goalie",
                "shots",
                "xg",
                "power_play",
                "penalty_kill",
                "royal_road",
            ],
        }

        general_math_terms = [
            "regression",
            "linear",
            "logistic",
            "ridge",
            "lasso",
            "poisson",
            "bivariate",
            "monte_carlo",
            "simulation",
            "bayesian",
            "elo",
            "markov",
            "z_score",
            "standard_deviation",
            "correlation",
            "kelly",
            "staking",
            "edge",
            "ev",
            "expected_value",
            "implied_probability",
            "no_vig",
            "fair_probability",
            "closing_line",
            "clv",
            "risk",
            "variance",
        ]

        technique_patterns = {
            "Implied probability": ["implied_probability", "american_to_prob", "odds_to_prob"],
            "No-vig / fair probability": ["no_vig", "novig", "fair_probability", "remove_vig"],
            "Expected value / EV": ["expected_value", "ev", "edge"],
            "Kelly / staking": ["kelly", "stake", "staking"],
            "Risk management": ["risk", "bankroll", "exposure"],
            "Linear regression": ["linear_regression", "linear regression"],
            "Logistic regression": ["logistic_regression", "logistic regression"],
            "Ridge / Lasso regression": ["ridge", "lasso"],
            "Poisson model": ["poisson"],
            "Bivariate Poisson": ["bivariate"],
            "Monte Carlo simulation": ["monte_carlo", "simulation"],
            "Bayesian model": ["bayesian"],
            "Elo / rating model": ["elo", "rating"],
            "Markov model": ["markov"],
            "Correlation model": ["correlation"],
            "Possession model": ["possession"],
            "Pace model": ["pace"],
            "Four Factors": ["four factors", "efg", "turnover", "rebound", "free_throw"],
            "Shot quality": ["shot_quality", "shot quality"],
            "Fatigue / rest adjustment": ["fatigue", "rest", "travel"],
            "Injury / minutes adjustment": ["injury", "minutes", "usage"],
            "Market weakness detector": ["market_weakness", "weakness"],
            "CLV / closing line value": ["clv", "closing_line"],
        }

        def simple_signature(node: Any) -> str:
            try:
                args = []
                all_args = list(getattr(node.args, "posonlyargs", [])) + list(node.args.args)
                for arg in all_args:
                    args.append(arg.arg)
                if node.args.vararg:
                    args.append("*" + node.args.vararg.arg)
                for arg in node.args.kwonlyargs:
                    args.append(arg.arg)
                if node.args.kwarg:
                    args.append("**" + node.args.kwarg.arg)
                return "(" + ", ".join(args) + ")"
            except Exception:
                return "()"

        def short_doc(node: Any) -> str:
            doc = ast.get_docstring(node) or ""
            doc = " ".join(doc.split())
            return doc[:300]

        sport_key = sport.lower()
        keywords = sport_keywords.get(sport_key, []) + general_math_terms

        modules = []
        techniques_found = set()
        files_checked = 0

        for path in root.rglob("*.py"):
            rel = path.relative_to(root)
            rel_text = str(rel).replace("\\", "/")
            parts = set(rel.parts)

            if parts & exclude_dirs:
                continue

            if path.name == "main.py":
                continue

            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lower_text = text.lower()
            lower_rel = rel_text.lower()

            is_priority = path.name in priority_files or any(
                lower_rel.startswith(directory.lower() + "/") for directory in priority_dirs
            )
            sport_match = any(keyword.lower() in lower_text or keyword.lower() in lower_rel for keyword in keywords)

            if not include_all and not is_priority and not sport_match:
                continue

            try:
                tree = ast.parse(text)
            except Exception as error:
                modules.append({
                    "module": rel_text,
                    "parse_error": str(error),
                    "functions": [],
                    "classes": [],
                    "techniques": [],
                })
                continue

            module_techniques = []
            for label, patterns in technique_patterns.items():
                if any(pattern.lower() in lower_text for pattern in patterns):
                    module_techniques.append(label)
                    techniques_found.add(label)

            functions = []
            classes = []

            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append({
                        "name": node.name,
                        "signature": simple_signature(node),
                        "doc": short_doc(node),
                    })

                if isinstance(node, ast.ClassDef):
                    methods = []
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            methods.append({
                                "name": item.name,
                                "signature": simple_signature(item),
                                "doc": short_doc(item),
                            })

                    classes.append({
                        "name": node.name,
                        "doc": short_doc(node),
                        "methods": methods[:30],
                    })

            if functions or classes or module_techniques:
                modules.append({
                    "module": rel_text,
                    "techniques": module_techniques,
                    "functions": functions[:40],
                    "classes": classes[:20],
                })

            files_checked += 1

            if files_checked >= max_files:
                break

        return {
            "ok": True,
            "sport": sport,
            "mode": "repo_math_catalog",
            "message": "This lists math/model/regression code found in your repo. It does not execute bets.",
            "files_checked": files_checked,
            "modules_found": len(modules),
            "techniques_found": sorted(list(techniques_found)),
            "modules": modules,
        }

    @app.get("/odds/opportunities/live")
    async def odds_opportunities_live(
        sport: str = "basketball_nba",
        regions: str = "us",
        markets: str = "h2h,spreads,totals",
        odds_format: str = "american",
        limit: int = 30,
        arb_stake: float = 100.0,
        near_arb_max_hold_percent: float = 1.25,
        value_edge_min_percent: float = 0.25,
        middle_min_width: float = 0.5,
    ):
        from src.core.opportunity_scanner import scan_opportunities

        payload = await PROVIDER_ROUTER.get_odds_events(
            "the_odds_api",
            sport,
            None,
            regions=regions,
            markets=markets,
            odds_format=odds_format,
            limit=limit,
        )
        if not payload.get("ok"):
            status_code = int(payload.get("status_code") or 500)
            error = (
                "Missing THE_ODDS_API_KEY or ODDS_API_KEY"
                if payload.get("error_type") == "PROVIDER_NOT_CONFIGURED"
                else str(payload.get("message") or "The Odds API provider request failed.")
            )
            return JSONResponse(
                status_code=status_code,
                content={"ok": False, "provider": "The Odds API", "status_code": status_code, "error": error},
            )
        events = payload.get("raw_response") if isinstance(payload.get("raw_response"), list) else []
        scan = scan_opportunities(
            events,
            stake=arb_stake,
            min_edge=value_edge_min_percent / 100.0,
            near_arb_max_hold_percent=near_arb_max_hold_percent,
            middle_min_width=middle_min_width,
        )
        return {
            "ok": True,
            "source": "The Odds API",
            "sport": sport,
            "regions": regions,
            "markets": markets,
            "events_checked": len(events),
            **scan,
        }

    @app.get("/model/live-card")
    async def model_live_card(
        sport: str = "basketball_nba",
        market: str = "h2h",
        min_edge: float = 0.01,
        regions: str = "us",
        odds_format: str = "american",
        limit: int = 25,
    ):
        return await MODEL_CARD_SERVICE.assemble_live_card(
            sport=sport,
            market=market,
            min_edge=min_edge,
            regions=regions,
            odds_format=odds_format,
            limit=limit,
        )
